# sigma2

sigma2 为金融市场数据提供有状态的逐条算子。Signal 的结果属于当前观测；Outcome 在等待固定数量的后续观测后，输出属于历史锚点的结果。计算生命周期位于 `sigma2.core`，不依赖具体市场数据模块。指标公式和输出空间复用 pyta2。

## 安装

需要 Python 3.10+。在仓库根目录安装：

```bash
python -m pip install -e .
```

项目依赖固定到 pyta2 提交 `65071a84099c30a4d9476c327232da7c057b2caa`，安装时需要能够通过 SSH 访问对应仓库。

## 单 symbol K 线

K 线算子使用相同的固定输入，每次返回字典：

```python
from sigma2 import rKlineMA

ma = rKlineMA(2, ma_type="SMA", field="close")
ma.step(10, 10, 10, 10, open_time=0)
ma.step(20, 20, 20, 20, open_time=1)
print(ma.step(30, 40, 30, 40, open_time=2))  # {'ma': 30.0}
print(ma.g_index, ma.meta_info["used_fields"])  # 2 ('close',)
```

`step(open, high, low, close, volume=None, *, open_time=None, is_missing=False)` 中，OHLC 必须提供，`volume` 可以省略；时间和缺失标记使用关键字。`is_missing=True` 表示整根 K 线缺失；选择成交量作为计算输入时，`volume=None` 也作为缺失值。数据格式由上游保证，`used_fields` 是元信息，不参与逐条校验。

每次 `step()` 都处理一根新 K 线。上游须按顺序提供已确定的数据，并过滤同一根 K 线的盘中更新和重复消息；`open_time` 不用于检查重复或顺序。历史数据修订时，创建新实例并从可靠数据重放。各实例独立处理一条 symbol 数据流。

提供的单 K 线 Signal 和批量函数包括：

| 分类 | 逐条算子 | 批量函数 |
| --- | --- | --- |
| 价格 | `rKlineReturn`、`rKlineGap` | `KlineReturn`、`KlineGap` |
| 趋势 | `rKlineMA`、`rKlineMACD`、`rKlineMACross` | `KlineMA`、`KlineMACD`、`KlineMACross` |
| 动量 | `rKlineRSI`、`rKlineKDJ` | `KlineRSI`、`KlineKDJ` |
| 波动 | `rKlineATR`、`rKlineBoll` | `KlineATR`、`KlineBoll` |
| 成交量 | `rKlineOBV`、`rKlineMFI`、`rKlineVWAP` | `KlineOBV`、`KlineMFI`、`KlineVWAP` |

MA 及使用 MA 的指标支持 SMA、EMA、WMA、HMA、DEMA、TEMA 和 ZLEMA；均线只接收一个周期参数。VWAP 使用滚动窗口，不按交易日重置。指标的预热和缺失后的恢复由 pyta2 决定。

## 时间参数命名

| 名称 | 含义 | 示例 |
| --- | --- | --- |
| `n` | 单周期技术指标的周期参数 | `rKlineMA(n=5)` |
| `lag` | 当前观测与过去参考观测之间的逻辑步数 | `rKlineReturn(lag=5)` |
| `n_backward` | 结果位置之前所需的历史观测数 | core 元信息，由算法决定 |
| `n_forward` | 结果位置之后需要等待的观测数 | 未来结果的构造参数及 core 元信息 |
| `history_window` | 提供给下游指标的输入历史长度 | pyta2 桥接参数 |
| `buffer_size` | 保留的输出结果数量 | `0` 不缓存，`-1` 无限缓存 |

例如，SMA 的 `n=5` 使用当前值及之前 4 个值；EMA 的 `n` 还决定平滑系数，递推状态可能受到更早数据影响。`lag=5` 则比较 `t` 与 `t-5` 两个位置的价格，跨越 6 个逻辑位置；中间价格缺失不改变端点。`lag` 按 K 线或 Bundle 截面推进的步数计算，不代表实际时长，`open_time` 不会自动补齐缺失时点。

`n_backward` 和 `n_forward` 描述算法的时序依赖，`min_periods = n_backward + 1 + n_forward`；不能假定它们与所有指标的 `n` 或 `lag` 相等。它们和 `buffer_size` 在构造时确定，运行中不可修改。多个指标周期按含义命名，例如 MACD 的 `fast`、`slow`、`signal`。KDJ 目前仍使用 `n1`、`n2`、`n3`，其具体命名另行确定。完整规范见[时间参数命名设计](docs/design/time-parameter-naming-20261030-overview.md)。

## 批量重放

批量函数接收逐条字典，字段与对应 `step` 一致。默认返回以输出字段名为键的 NumPy 数组字典：

```python
from sigma2 import KlineMA

bars = [
    {"open": 10, "high": 11, "low": 9, "close": 10, "open_time": 0},
    {"open": 11, "high": 12, "low": 10, "close": 11, "open_time": 1},
]
columns, meta = KlineMA(bars, 2, return_meta_info=True)
print(columns["ma"], meta["full_name"])
```

`return_type` 还支持 `tuple`、`list`、`dataframe` 和 `pl.dataframe`。每条成功处理的输入对应一行。`forward_step_apply(bars, operator)` 也可用于自定义算子，并从传入实例的当前状态继续；输出格式和所需依赖会在重放前检查。批量整理过程中发生异常时，之前成功处理的输入已经推进算子。未声明 schema、多维输出或以 `None` 表示缺失的字段按 object 列存储。

## 多 symbol 收益率排名

`rKlineBundleReturnRank` 按每个 symbol 的 `lag` 步收盘收益率排名，收益率为 `close_t / close_(t-lag) - 1`：

```python
from sigma2 import rKlineBundleReturnRank

first = {
    "BTC": {"open": 100, "high": 101, "low": 99, "close": 100},
    "ETH": {"open": 200, "high": 201, "low": 199, "close": 200},
    "SOL": {"open": 100, "high": 101, "low": 99, "close": 100},
}
second = {
    "BTC": {"open": 110, "high": 111, "low": 109, "close": 110},
    "ETH": {"open": 220, "high": 221, "low": 219, "close": 220},
    "SOL": {"open": 90, "high": 91, "low": 89, "close": 90},
}
rank = rKlineBundleReturnRank(lag=1)
rank.step(first, open_time=0)  # 预热，所有排名为 NaN
print(rank.step(second, open_time=1))
# {'rank': {'BTC': 2, 'ETH': 3, 'SOL': 1}}
print(rank.meta_info["used_fields"])  # ('close',)
```

`step(bundle, *, open_time=None, has_missing=False)` 将每次输入视为已确认的截面；调用方负责时间顺序和去重。`lag` 为正整数，表示回看的截面步数，默认从低到高排名；`ascending=False` 改为从高到低。排序稳定，相同收益率按当前 Bundle 的输入顺序分配不同名次。需要先收到 `lag` 个截面作为历史；当前或参考 close 为 None、非有限、被标记缺失，或者参考价为零时，该 symbol 的排名为 NaN。只使用两个端点，中间截面的缺失不改变结果。

每次 `step` 推进一个共同时间位置；调用方需按统一周期提供截面。完全缺失的时点应传入空 Bundle，避免时间轴被压缩；`open_time` 不自动补齐时点。输出只包含当前输入中的 symbol，参考截面没有的 symbol 得到 NaN。`has_missing` 是截面信息，不推断缺少哪些 symbol。

批量入口 `KlineBundleReturnRank` 接收包含 `bundle` 和可选 `open_time`、`has_missing` 的字典序列；默认结果的 `rank` 是 object 数组，每一项是一个 symbol 排名字典。空输入返回空字典。排名结果与实例的 object 缓存共享嵌套字典，使用时应视其为只读。独立示例见 `examples/401_bundle_return_rank.py`。

## 多 symbol 加权价格指数

固定权重和实时市值分别使用 `rKlineBundleFixedWeightIndex`、`rKlineBundleMarketCapWeightedIndex` 计算当期价格的加权平均：`sum(price * weight) / sum(weight)`。固定权重在初始化时提供；市值从每个 symbol 当期的 `market_cap` 获取：

```python
from sigma2 import rKlineBundleFixedWeightIndex, rKlineBundleMarketCapWeightedIndex

bundle = {
    "BTC": {"open": 100, "high": 101, "low": 99, "close": 100, "market_cap": 300},
    "ETH": {"open": 200, "high": 201, "low": 199, "close": 200, "market_cap": 100},
}
fixed = rKlineBundleFixedWeightIndex({"BTC": 1, "ETH": 1})
market_cap = rKlineBundleMarketCapWeightedIndex()
print(fixed.step(bundle, open_time=1))       # {'index': 150.0}
print(market_cap.step(bundle, open_time=1))  # {'index': 125.0}
print(market_cap.meta_info["used_fields"])   # ('close', 'market_cap')
```

固定权重在计算时归一化，必须非负且至少一个为正；`weights` 属性返回原始正权重成分的副本。`has_missing=False` 时，调用方保证参与成分的价格完整且为有限数值，市值模式还须保证市值完整、有限且非负；算子直接计算，不逐项检查。数据缺失或无效时，数据源须设置 `has_missing=True`。

`has_missing=True` 时，固定权重模式检查正权重成分，缺少成分、标记缺失或价格无效则返回 NaN；缺失的非成分不影响结果。市值模式直接返回 NaN，因为算子无法推断没有传入的 symbol；市值模式的空截面和全部市值为零也返回 NaN。零权重或零市值不参与加权，固定权重中没有的 symbol 不影响结果。

结果与价格单位相同，不使用基点。市值和成分变化会影响结果，所以它不能直接当作只反映价格涨跌的收益指数。批量入口分别为 `KlineBundleFixedWeightIndex` 和 `KlineBundleMarketCapWeightedIndex`；完整示例见 `examples/402_bundle_weighted_index.py`。

权重比例或价格贡献极小时，使用精确分数累计这些贡献，再转成浮点；最终输出仍受浮点数的表示范围和舍入限制。

## 未来结果

`rKlineFutureReturn`、`rKlineFutureChange`、`rKlineFutureHighLowChange` 和 `rKlineATRBoundTrigger` 使用 K 线的同一输入接口。`n_forward` 是等待的后续观测数；每次调用后 `result_index = g_index - n_forward`，结果属于该锚点。`result_index < 0` 时尚没有锚点结果。

```python
from sigma2 import forward_step_apply, rKlineFutureReturn

bars = [
    {"open": p, "high": p, "low": p, "close": p, "open_time": i}
    for i, p in enumerate([10, 11, 13, 12])
]
result = forward_step_apply(bars, rKlineFutureReturn(2, buffer_size=0))
print(result["return"])  # 结果按锚点回填，最后两项尚未成熟
```

批量结果的每一行对应本次输入的逻辑观测。尾部未成熟位置使用 schema 的缺失值；整数类型可能使用整数哨兵。继续已有状态重放时，本次输入之前的锚点不包含在返回表中。回填后的未来结果仅在对应后续观测到达时才可用。

## 盘口、成交和自定义信号

```python
from sigma2 import rBookSpread, rTradeSignedVolume

spread = rBookSpread()
print(spread.step(bids=[(100, 2)], asks=[(101, 1)]))  # {'spread': 1.0}
volume = rTradeSignedVolume()
print(volume.step(price=100, volume=3, side="sell"))  # {'signed_volume': -3.0}
```

盘口价差使用最高买价和最低卖价，档位不必预先排序；任一侧为空时返回 NaN。

自定义算子继承数据类型对应的基类并实现 `forward`，返回字典即可；子指标、输入窗口和递推数值使用普通实例属性。`step()` 中的计算、输出字段检查或缓存写入失败后，实例被锁定，应新建实例并重放；失败实例的索引和缓存不保证可用。数据类型入口在推进前拒绝的输入不会锁定实例。实例不保证并发或重入安全。可用 `schema`、`n_backward`、`buffer_size` 和 `used_fields` 指定元信息与缓存；不指定 schema 时，输出字段由首次结果确定，缓存使用 object 类型。

## pyta2 桥接

`pyta2_signal()` 和 `rPyta2Signal` 可将其他 pyta2 `rIndicator` 绑定到 K 线字段。调用者指定指标参数、输入字段和 `history_window`，并负责确认该指标支持所提供的有限窗口。桥接不额外修改指标的缺失处理。

## 当前范围与示例

`examples/001_kline_ma.py` 是均线示例；其余示例分别展示趋势、动量、波动、量价、价格变化、缺失数据、盘口成交、未来结果、pyta2 桥接、自定义信号、ATR 边界、截面排名和加权价格指数。文件名按 K 线、盘口、成交、未来结果和截面分级编号，每个示例自带数据，可以独立运行。

旧 `sigma2.batch`、旧 Bundle 实现及相关输入辅助已归档至 `docs/backup/v-0.11/`；当前 Bundle 提供 Signal 基类、收益率排名和加权价格指数。现有 `tests/` 仍使用旧接口，尚未迁移到当前契约。设计见[算子单向推进与失败锁定](docs/design/operator-single-pass-20261031-overview.md)、[K 线截面收益率排名](docs/design/kline-bundle-return-rank-20261030-overview.md)、[加权价格指数](docs/design/kline-bundle-weighted-index-20261030-overview.md)及[旧 batch 与遗留依赖清理](docs/design/retire-legacy-batch-20261030-overview.md)。
