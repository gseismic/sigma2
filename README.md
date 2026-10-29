# sigma2

sigma2 为金融市场事件提供逐条推进的 Signal 和 Outcome。Signal 的结果属于当前观测；Outcome 等待固定数量的后续观测后，输出属于历史锚点的结果。量化研究和训练系统可以消费这些结果，核心不依赖训练目标的概念。

项目按输入数据分包：`sigma2.kline` 处理单 symbol K 线，`sigma2.kline_bundle` 处理同一时点的多 symbol 截面，`sigma2.orderbook` 和 `sigma2.trade` 分别处理盘口快照和逐笔成交。

> 2026-10-29：core 和单 K 线 `rKlineMA` 已改为新的 `step` 契约。其他指标、Bundle、Outcome 和通用批量接口尚未迁移，可能因 core 或 K 线基类变化而不能工作；本文这些部分的旧示例仅供后续迁移参考。`KlineMA` 批量入口暂不可用。新设计见 [core 与单 K 线 MA 设计](docs/design/kline-step-core-20261029-overview.md)。

## 安装

需要 Python 3.10+。在仓库根目录安装：

```bash
python -m pip install -e .
```

当前 pyta2 的新旧接口都使用 `0.0.1` 版本号，项目依赖固定到 pyta2 提交 `93ab75884e137bc4133b9445bc900a0a8468624c`，安装时需要能够通过 SSH 访问对应仓库。该 pyta2 提交的包初始化会使用 SciPy，因此 sigma2 显式声明 SciPy 依赖。

## 单 symbol K 线

`rKlineMA` 接收固定的行情字段，每次返回一个字典。`volume` 可省略；`open_time`、`is_closed` 和 `is_missing` 为关键字参数。上游负责提供符合约定的数值和顺序。

```python
from sigma2.kline import rKlineMA

signal = rKlineMA(2, ma_type="EMA", field="close", symbol="BTCUSDT")
signal.step(100, 101, 99, 100, open_time=1)
preview = signal.step(100, 109, 99, 108, open_time=2, is_closed=False)
result = signal.step(100, 111, 99, 110, open_time=2, is_closed=True)
print(preview, result)        # {'ma': 104.0} {'ma': 105.0}
print(signal.g_index)         # 1：第二根 K 线只推进一次
print(signal.used_fields)     # ('close',)
```

`is_closed=False` 可以多次更新同一根尚未结束的 K 线；最后传入 `is_closed=True` 确认。省略 `open_time` 时，调用方须保证这些更新对应同一根 K 线。`is_missing=True` 表示整根 K 线缺失；选择 `field="volume"` 时，省略 volume 按缺失数值处理。`used_fields` 是随构造参数变化的元信息，不参与输入检查。

均线只接受一个算法参数 `n`，类型支持 SMA、EMA、WMA、HMA、DEMA、TEMA 和 ZLEMA。每个实例消费一个 symbol 的输入流，`symbol` 用于构造因子名称。

### 公式名和因子名

```python
from sigma2 import rKlineMA

signal = rKlineMA(14, symbol="BTCUSDT")
print(signal.full_name)      # SMA(14)[close]
print(signal.formula_names)  # ['SMA(14)[close]']，物理表可共享的公式列名
print(signal.factor_names)   # ['BTCUSDT:SMA(14)[close]']，带作用域的结果名
```

逐步结果的键是 schema 字段，例如 `ma`。作用域在构造时确定；未指定 symbol 时单 K 线算子使用未加前缀的公式名。`formula_names` 的顺序与 schema 输出字段一致，多输出会在公式名后加 `.字段名`。

按 `(symbol, open_time)` 保存行式数据时，可存储共享的 `formula_names`，在读取时通过 `qualify_factor_name(symbol, formula_name)` 组合训练列名。symbol、公式和数据来源应分别保存，不应靠拆分结果字符串恢复身份。

### 以下为尚未迁移的历史说明

下面的其他指标、截面、Outcome、批量与旧生命周期描述保留作迁移参考，尚不符合本次 core 的接口。

### 常用指标

`sigma2.kline` 提供 `rKlineMA`、`rKlineRSI`、`rKlineMACD`、`rKlineBoll`、`rKlineKDJ`、`rKlineATR`、`rKlineMACross`、`rKlineOBV`、`rKlineMFI`、`rKlineVWAP` 及其 `KlineX` 批量函数。均线、指标公式和 ATR 边界扫描复用 pyta2；K 线输入、字段映射和逐条生命周期由 sigma2 管理。`KlineVWAP(n)` 是最近窗口的成交量加权典型价格，不按交易日重置；OBV、MFI、VWAP 需要 volume。

批量接口按输入顺序重放同一个 `step()`，接受逐行字典序列、列式字典或 DataFrame，默认返回以 `factor_names` 为键的 NumPy 数组字典。`return_type` 还支持 `tuple`、`list`、`dataframe` 和 `pl.dataframe`；`return_meta_info=True` 返回结果和元信息。原有 `KlineBar` 输入仍可使用，其时间和 symbol 校验保持不变。

## 多 symbol 截面

Bundle 字典是同一逻辑时点的多 symbol 快照。固定的 `symbols` 定义结果顺序；当前时点没有行情的 symbol 不放进 `bundle`。数据源负责保证各标的属于同一时点并确认快照何时可以放行。

```python
from sigma2.kline_bundle import rKlineBundleMA, rKlineBundleRank

symbols = ("BTC", "ETH", "SOL")
snapshot = {
    "open_time": 1,
    "bundle": {
        "BTC": {"open": 100, "high": 101, "low": 99, "close": 100},
        "ETH": {"open": 200, "high": 201, "low": 199, "close": 200},
    },
}
rank = rKlineBundleRank(symbols=symbols, return_dict=True)
ma = rKlineBundleMA(2, symbols=symbols, return_dict=True)
print(rank.step(snapshot))  # {'rank': [1., 2., nan]}，输出值为 NumPy 数组
print(ma.step(snapshot))    # 第一个快照尚未满足均线预热
```

快照和每个存在的 Bar 都接受字典或其他 `Mapping`，Bar 使用单 K 线字段规则；若提供 `symbol`，必须与 `bundle` 的对应键一致。未知 symbol 会报错。排名只包含当前字段有效的 symbol，平局使用平均名次。`rKlineBundleReturnRank(n)` 计算过去 N 个共同快照的收益，再在截面上排名。要对其他单 K 线 Signal 计算整个截面，可使用 `rKlineBundleMapSignal`；它为每个 symbol 创建独立状态，缺失 Bar 使用显式占位推进共同时间。

`open_time` 可省略；存在时默认作为快照行情时间。Bundle 的 `key_map` 作用于每个 Bar，`bundle_key_map` 作用于快照顶层，例如 `{"bundle": "klines", "open_time": "date"}` 分别读取输入的 `klines` 和 `date`。映射优先于同名键；映射的可选时间缺失时不回退。批量字典输入需通过 `symbols=` 或首个快照的 `symbols` 明确提供完整全集，不从可能缺失标的的首个快照推断。

Batch 结果的每个字段形状是 `(时间, symbol)`；`Space` 描述一个 symbol 的值，symbol 顺序由算子配置和元信息提供。多维 Space 的结果在 symbol 轴后继续保留其形状。DataFrame 格式按 `(bar_time, symbol)` 展开；行情时间缺失或部分缺失时使用 `(g_index, symbol)`。

## 未来结果与时间

```python
from sigma2.kline_bundle import KlineBundleFutureReturn, rKlineBundleFutureReturn

symbols = ("BTC", "ETH")
ordered_bundles = []
for i, prices in enumerate([(100, 200), (110, 190), (121, 210)]):
    bars = {
        symbol: {"open": price, "high": price, "low": price, "close": price}
        for symbol, price in zip(symbols, prices)
    }
    ordered_bundles.append({"open_time": i, "available_at": i + 1, "bundle": bars})

outcome = rKlineBundleFutureReturn(2, symbols=symbols, return_dict=True)
for bundle in ordered_bundles:
    value = outcome.step(bundle)
    if outcome.result_index >= 0:
        print(outcome.result_index, value)

columns, meta = KlineBundleFutureReturn(
    ordered_bundles, 2, symbols=symbols, return_meta_info=True
)
```

`n_forward=2` 表示等待 2 个输入快照，不自动等同于 2 个自然日。未来收益要求锚点及全部未来区间的对应字段有效，符合当前 pyta2 的缺失规则。在线缓存按结果产生顺序保存；batch 按 `result_index` 回填历史锚点，末尾未成熟位置为缺失值。单 K 线也可使用 `rKlineFutureReturn` 和 `forward_outcome_apply()`。

单 K 线 `rKlineATRBoundTrigger` 使用锚点 ATR 定义边界，固定观察期结束后给出 `trigger`、`unit_change` 和 `trigger_location`，字段名称与 pyta2 Effect 一致。窗口中存在无效 OHLC 时结果为 schema 缺失值。

`bar_time` 是输出元信息和索引中使用的通用行情时间名称；Bundle 字典默认从 `open_time` 读取，单 K 线字典从 `bar_time` 或显式映射读取。`available_at` 是来源确认 Bar 或 Bundle 可用的时间。两者均可省略，sigma2 不根据 `open_time` 猜测 `available_at`。batch 元信息中的 `result_input_ready_at` 是所有先前输入最早齐备时间，不包含计算和发布延迟；无法确定时为 `None`。结果的实际可用时间需要由运行或消费层记录；按锚点回填的未来结果不能视为锚点时已知。

## 生命周期与 schema

- `rOperator` 提供共同生命周期，`rSignal` 固定 `n_forward=0`，`rOutcome` 要求 `n_forward>=1`；`result_index = g_index - n_forward`。
- `schema` 直接使用 pyta2 的 `Schema` 与 `Space`。逐条原始返回值、`return_dict`、字段顺序和 `missing_output` 沿用 pyta2 语义；Bundle 的 symbol 轴由 family 添加。
- 输出缓存默认保存最近一步，`buffer_size=0` 或 `None` 关闭，`-1` 无限，正数保存最近 N 步。Bundle 缓存逐 symbol 使用 pyta2 标量表，`outputs[key]` 以时间和 symbol 两个轴查看。
- 修改已处理数据或计算失败后，调用 `reset()` 并从已确认输入序列重放。重置失败时实例保持 faulted；算子状态与输出缓存不是数据源的持久化存储。
- Bundle 的 symbol 结果顺序在一个运行段内固定。字典输入的时序、周期和共同时间由上游保证。要改变 symbol 集合，建立新运行段；需要连续历史时按新集合重放。

## 从 0.6.0 迁移

- 单 K 线 `step(**ohlcv)` 改为 `step(bar)`，直接传入行情字典；横截面使用包含 `bundle` 的字典。
- 未来计算从 `sigma2.kline.target` 迁至 `sigma2.kline.outcome`，`horizon` 改名为 `n_forward`，批量使用 `forward_outcome_apply()`；旧路径不再提供。
- 自定义算子的 schema 改用 pyta2 `Space`，窗口元信息改为 `n_backward`、`n_forward` 和 `min_periods`。输出缓存默认仅保留最近一步，原来依赖无限缓存的调用方需设置 `buffer_size=-1`。

### 预热

`n_backward` 表示结果所属位置之前需要的最少观测数，`n_forward` 表示结果所属位置之后需要等待的观测数，`min_periods = n_backward + 1 + n_forward`。例如：

```python
from sigma2.kline import rKlineMA

signal = rKlineMA(20, ma_type="SMA")
print(signal.n_backward)  # 19：当前结果之前至少需要 19 根
print(signal.min_periods)  # 20：包括结果所属的当前 K 线
```

旧的 `required_window` 与新的 `n_backward` 是否相差一根取决于原算法及其窗口定义，迁移时应核对计数边界。观测数按实际输入步数计算；如果行情存在缺口，向前读取相同分钟数不一定得到所需根数。EMA 等递推算法的 `n_backward` 只是开始产生完整输出的最小预热要求；若要和持续运行的实例精确一致，应从相同起点重放相同数据。

## 示例与扩展

安装项目及依赖后，在 `examples` 目录运行示例，例如：

```bash
cd examples
python 09_kline_bundle.py
```

其余例子按 `01` 至 `08` 展示单 K 线、盘口、成交、未来结果、pyta2 组合和自定义 Signal；`10_mapping_inputs.py` 展示字典和字段映射。扩展时参考 [新增信号指南](skills/sigma2-usage/references/add-signals.md)、[截面字典结构](docs/design/bundle-snapshot-20261028-overview.md)、[字典输入设计](docs/design/step-mapping-20261028-overview.md)、[核心设计](docs/design/sigma2-operator-signal-outcome-20261028-overview.md) 和 [KlineBundle 设计](docs/design/kline-bundle-20261028-overview.md)。

通用 `pyta2_signal()` 需要显式 `history_window`；调用者应确认具体 pyta2 指标支持该有限窗口。部分 pyta2 指标和 effect 尚未迁移到新基类，不能假定它们均可用于桥接。
