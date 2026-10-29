# sigma2

sigma2 为金融市场数据提供有状态的逐条算子。Signal 的结果属于当前观测；Outcome 在等待固定数量的后续观测后，输出属于历史锚点的结果。计算生命周期位于 `sigma2.core`，不依赖具体市场数据模块。指标公式和输出空间复用 pyta2。

## 安装

需要 Python 3.10+。在仓库根目录安装：

```bash
python -m pip install -e .
```

项目依赖固定到 pyta2 提交 `93ab75884e137bc4133b9445bc900a0a8468624c`，安装时需要能够通过 SSH 访问对应仓库。

## 单 symbol K 线

K 线算子使用相同的固定输入，每次返回字典：

```python
from sigma2 import rKlineMA

ma = rKlineMA(2, ma_type="SMA", field="close")
ma.step(10, 10, 10, 10, open_time=0)
ma.step(20, 20, 20, 20, open_time=1)
print(ma.step(30, 30, 30, 30, open_time=2, is_closed=False))  # {'ma': 25.0}
print(ma.step(30, 40, 30, 40, open_time=2, is_closed=True))   # {'ma': 30.0}
print(ma.g_index, ma.meta_info["used_fields"])  # 2 ('close',)
```

`step(open, high, low, close, volume=None, *, open_time=None, is_closed=True, is_missing=False)` 中，OHLC 必须提供，`volume` 可以省略；时间和状态使用关键字。`is_missing=True` 表示整根 K 线缺失；选择成交量作为计算输入时，`volume=None` 也作为缺失值。数据格式由上游保证，`used_fields` 是元信息，不参与逐条校验。

`is_closed=False` 允许多次更新同一根 K 线，最后使用 `is_closed=True` 确认。若上一根尚未确认就收到不同的 `open_time`，或已确认后再次收到相同的 `open_time`，算子会报错。省略 `open_time` 时，调用方须保证观测更新顺序。各实例独立处理一条 symbol 数据流。

提供的单 K 线 Signal 和批量函数包括：

| 分类 | 逐条算子 | 批量函数 |
| --- | --- | --- |
| 价格 | `rKlineReturn`、`rKlineGap` | `KlineReturn`、`KlineGap` |
| 趋势 | `rKlineMA`、`rKlineMACD`、`rKlineMACross` | `KlineMA`、`KlineMACD`、`KlineMACross` |
| 动量 | `rKlineRSI`、`rKlineKDJ` | `KlineRSI`、`KlineKDJ` |
| 波动 | `rKlineATR`、`rKlineBoll` | `KlineATR`、`KlineBoll` |
| 成交量 | `rKlineOBV`、`rKlineMFI`、`rKlineVWAP` | `KlineOBV`、`KlineMFI`、`KlineVWAP` |

MA 及使用 MA 的指标支持 SMA、EMA、WMA、HMA、DEMA、TEMA 和 ZLEMA；均线只接收一个周期参数。VWAP 使用滚动窗口，不按交易日重置。指标的预热和缺失后的恢复由 pyta2 决定。

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

`return_type` 还支持 `tuple`、`list`、`dataframe` 和 `pl.dataframe`。重放时同一未结束观测的多次更新只占一行。`forward_step_apply(bars, operator)` 也可用于自定义算子，并从传入实例的当前状态继续；目前表格收集面向标量输出。

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

批量结果的每一行对应本次输入的逻辑观测。尾部未成熟位置使用 schema 的缺失值；整数类型可能使用整数哨兵。继续已有状态重放时，本次输入之前的锚点不包含在返回表中。回填后的未来结果仅在对应后续观测到达时才可用；未结束 K 线参与计算时，结果只是预览。

## 盘口、成交和自定义信号

```python
from sigma2 import rBookSpread, rTradeSignedVolume

spread = rBookSpread()
print(spread.step(bids=[(100, 2)], asks=[(101, 1)]))  # {'spread': 1.0}
volume = rTradeSignedVolume()
print(volume.step(price=100, volume=3, side="sell"))  # {'signed_volume': -3.0}
```

自定义算子继承数据类型对应的基类并实现 `forward`，返回字典即可。需要保存的可变计算状态应放入 `self._state` 并通过它读取，基类负责初始状态、重算和 `reset()`；状态中的对象需要支持深复制。实例不保证并发或重入安全。可用 `schema`、`n_backward`、`buffer_size` 和 `used_fields` 指定元信息与缓存；不指定 schema 时，输出字段由首次结果确定，缓存使用 object 类型。

## pyta2 桥接

`pyta2_signal()` 和 `rPyta2Signal` 可将其他 pyta2 `rIndicator` 绑定到 K 线字段。调用者指定指标参数、输入字段和 `history_window`，并负责确认该指标支持所提供的有限窗口。桥接不额外修改指标的缺失处理。

## 当前范围与示例

`examples/001_kline_ma.py` 是均线示例；其余示例分别展示趋势、动量、波动、量价、价格变化、缺失数据、盘口成交、未来结果、pyta2 桥接、自定义信号和 ATR 边界。文件名按 K 线、盘口、成交和未来结果分级编号，每个示例自带数据，可以独立运行。

`kline_bundle` 和旧 `sigma2.batch` 尚未按当前 core 契约迁移，暂不可视为可用接口；它们仍依赖的 K 线输入辅助暂时保留。旧实现和失效示例归档于 `docs/backup/v-0.11/`。本轮设计见 [盘口、成交和单 K 线算子迁移](docs/design/data-families-step-20261030-overview.md)，core 与未结束观测设计见 [core 与单 K 线 MA](docs/design/kline-step-core-20261029-overview.md)。
