# sigma2

sigma2 是面向金融市场事件的有状态 Signal 与机器学习因子库，当前版本为 `0.4.0`。同一个 Signal 既能逐条处理事件，也能由批量接口逐行重放。pyta2 提供 rolling 指标；sigma2 负责 K 线、盘口、成交的输入语义、字段绑定、修订生命周期和最终因子名。

## 安装与运行

需要 Python 3.10+。在仓库根目录安装本包及 `numpy`、`pyta2` 依赖，然后运行示例：

```bash
python -m pip install -e .
python -m examples.01_kline_batch
```

### 第一次批量计算

下面的代码可以直接运行。批量接口接收带有 `open/high/low/close/volume` 五列的对象；普通 `dict`、pandas DataFrame 都可以。五列必须是一维、等长。

```python
from sigma2 import KlineMA

closes = [10.0, 11.0, 12.0, 13.0]
bars = {
    "open": closes,
    "high": closes,
    "low": closes,
    "close": closes,
    "volume": [1.0] * len(closes),
}

columns, meta = KlineMA(bars, 2, ma_type="SMA", return_meta_info=True)
name = meta["factor_names"][0]
print(name, columns[name][-1])  # SMA(2)[close] 12.5
```

默认结果为 `dict[str, numpy.ndarray]`。不足计算窗口的位置一般为 `NaN`。需要其它格式时传 `return_type="tuple"`、`"list"`、`"dataframe"` / `"pd.dataframe"` 或 `"pl.dataframe"`；DataFrame 格式分别需要 pandas 或 polars。

`rKlineMA` / `KlineMA` 可选择 SMA、EMA、WMA、HMA、DEMA、TEMA、KAMA、ZLEMA，并通过 `field` 绑定 `open/high/low/close/volume`。例如 [批量示例](examples/01_kline_batch.py) 同时计算收盘价均线和成交量均线。

### 在线推进与修订

一条 `step()` 输入是一根完整 K 线。行情源修订最后一根时，用相同字段调用 `update_last()`：

```python
from sigma2 import rKlineMA

signal = rKlineMA(2, ma_type="SMA", return_dict=True)
for close in (10.0, 11.0):
    signal.step(open=close, high=close, low=close, close=close, volume=1.0)

revised = signal.update_last(
    open=12.0, high=12.0, low=12.0, close=12.0, volume=1.0
)
print(float(revised["ma"]), signal.g_index)  # 11.0 1
```

`update_last()` 从该观测之前的检查点重算，不增加 `g_index`，也不追加输出行；连续修订只以最近一次 `step()` 为基准。每个实例只服务一条输入流。计算失败后实例会进入 faulted 状态，需要 `reset()` 并重放已确认数据。`forward()` 是子类计算钩子，不用于推进公共生命周期。

## 可运行示例

从仓库根目录按编号运行，例如 `python -m examples.02_kline_stream`：

| 场景 | 示例 | 内容 |
| --- | --- | --- |
| K 线批量 | [01_kline_batch.py](examples/01_kline_batch.py) | MA、MACD 多输出和元信息 |
| 在线修订 | [02_kline_stream.py](examples/02_kline_stream.py) | `step()`、重复 `update_last()`、批量重放 |
| 盘口与成交 | [03_market_events.py](examples/03_market_events.py) | 完整盘口快照与逐笔成交的不同输入签名 |
| 未来目标 | [04_future_target.py](examples/04_future_target.py) | 目标值对应历史 anchor 的位置 |
| pyta2 桥接 | [05_pyta2_bridge.py](examples/05_pyta2_bridge.py) | 将通用 ROC 绑定到 K 线并批量重放 |
| 自定义 Signal | [06_custom_signal.py](examples/06_custom_signal.py) | 自有递推状态、最后观测修订和批量重放 |

## 公共入口与输出身份

| 输入 family | 在线入口 | 批量入口或示例 |
| --- | --- | --- |
| K 线 | `rKlineMA`、`rKlineRSI`、`rKlineMACD`、`rKlineBoll`、`rKlineKDJ`、`rKlineATR`、`rKlineReturn`、`rKlineGap` | 同名去掉前缀 `r`，如 `KlineMA`、`KlineMACD` |
| 盘口快照 | `rBookSpread`，`step(bids=..., asks=...)` | [03_market_events.py](examples/03_market_events.py) |
| 逐笔成交 | `rTradeSignedVolume`，`step(price=..., volume=..., side=...)` | [03_market_events.py](examples/03_market_events.py) |
| 通用 pyta2 桥接 | `pyta2_signal()` / `rPyta2Signal` | `forward_signal_apply()` |

`bids`、`asks` 是已按价格排序的完整档位快照，档位形如 `(price, size)`；成交 `side` 为 `"buy"`、`"sell"` 或 `None`。K 线、盘口和成交 family 的 `update_last()` 与各自的 `step()` 使用同样的输入签名。

批量结果用 `factor_names` 作为列名：单输出是 `full_name`，多输出按 `full_name.output_key` 展开。例如 `rKlineMACD()` 的列名包括 `MACD(26,12,9)[close].dif`；逐条调用时 `return_dict=True` 则返回 `dif`、`dea`、`macd` 这些 schema key。`Kline` 只区分 Python API，不进入数据列身份。

pyta2 primitive 与 sigma2 Signal 可以并列导入：

```python
from pyta2.momentum import rRSI
from sigma2 import rKlineRSI

primitive = rRSI(14)
signal = rKlineRSI(14, field="close")
```

前者处理指标本身；后者处理 K 线字段绑定和 Signal 生命周期。通用桥接适合临时复用 pyta2 指标；稳定的公共 K 线因子优先使用具名 `rKlineX` / `KlineX` 入口。

## 未来目标与扩展

`sigma2.kline.target` 中的 `rKlineFutureReturn` 等目标依赖未来 K 线。以 horizon 为 2 的 future return 为例，在索引 2 收到第三根 K 线时，输出才确定索引 0 的目标值。它属于历史 anchor，不能作为索引 2 当下可用的特征；这些 target 也不支持普通正向 Signal 的 `update_last()` 语义。

扩展单个 pyta2 指标支撑的 K 线因子，参考 [K 线因子模板](docs/design/kline-factor-20260922-template.md)；扩展结构化或有状态 Signal，参考 [新增信号指南](skills/sigma2-usage/references/add-signals.md) 与 [06_custom_signal.py](examples/06_custom_signal.py)。当前总设计见 [sigma2 v5](docs/design/sigma2-20260922-v5.md)，最新计划执行记录见 [docs/dev/INDEX.md](docs/dev/INDEX.md)。
