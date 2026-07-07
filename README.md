# sigma2

sigma2 是面向金融时间序列和机器学习特征工程的 rolling signal 库。它不是 pyta2 的薄封装，也不是以 `FeatureSet` 为中心的应用框架；当前稳定核心是一套类似 `pyta2.base.rIndicator` 的轻量有状态 signal 基类体系。

## 项目定位

- `rSignal.step()` 是唯一公共状态推进入口，调用一次表示输入流推进一个新观测点或事件。
- `rSignal.forward()` 是子类计算 hook；直接调用不推进状态、不写输出缓存、不处理 `return_dict`。
- `core/` 是唯一核心目录，承载 `rSignal`、family 基类和 pyta2 通用信号基类。
- 根级 `kline/`、`orderbook/`、`trade/` 是信号分类目录，每个具体信号一个文件。
- `utils/` 只放 pyta2 resolver、导入兼容等辅助能力。
- 不保留 `base/`、`families/`、`signals/`、`adapters/` 作为公共源码结构。
- `FeatureData`、`ResearchDataset`、IC 分析、深度学习数据集、RL 环境和 minbt bridge 属于后续研究训练层能力，应消费 core，不定义 core。

## 当前结构

```text
sigma2/
  core/
    signal.py
    kline.py
    orderbook.py
    trade.py
    pyta2.py
  utils/
    pyta2.py
  kline/
    effect/
      future_return.py
      future_change.py
      future_high_low_change.py
      bound_trigger.py
    gap.py
    return_.py
    sma.py
    pyta2/sma.py
  orderbook/
    book_spread.py
  trade/
    trade_signed_volume.py
```

## 已实现能力

- `rSignal`
- `rKlineSignal`
- `rKlineWindowSignal`
- `rOrderBookSignal`
- `rTradeSignal`
- `rPyta2Signal`
- `rPyta2SMA`
- `rKlineFutureReturn`
- `rKlineFutureChange`
- `rKlineFutureHighLowChange`
- `rKlineBoundTrigger`
- `pyta2_signal()`
- `resolve_pyta2_indicator()`
- `register_pyta2_indicator()`
- `rReturn`
- `rGap`
- `rSMA`
- `rBookSpread`
- `rTradeSignedVolume`

## 导入示例

```python
from sigma2 import rPyta2SMA
from sigma2.core import rSignal, rKlineSignal
from sigma2.kline import rReturn, rGap, rSMA, rKlineFutureReturn
from sigma2.kline.effect import rKlineFutureReturn
from sigma2.kline.sma import rSMA
from sigma2.kline.pyta2 import rPyta2SMA
from sigma2.orderbook import rBookSpread
from sigma2.trade import rTradeSignedVolume
from sigma2.utils.pyta2 import resolve_pyta2_indicator
```

## 最小使用示例

```python
from sigma2 import rPyta2SMA

signal = rPyta2SMA(3, field="close", return_dict=True)

for price in [1.0, 2.0, 3.0]:
    row = signal.step(
        open=price,
        high=price,
        low=price,
        close=price,
        volume=1.0,
    )

print(row)  # {"ma": 2.0}
```

说明：`rPyta2SMA` 当前使用 pyta2 `rSMA`，因此输出 key 沿用 pyta2 schema，为 `ma`。如果需要纯 sigma2 示例信号，可使用 `rSMA`，输出 key 为 `sma`。

## K 线 effect target 示例

`sigma2.kline.effect` 是对 `pyta2.effect` 的 K 线 family 二层包装。用户仍然只输入标准 OHLCV：

```python
from sigma2.kline.effect import rKlineFutureReturn

target = rKlineFutureReturn(2, return_dict=True)

for price in [10.0, 11.0, 13.0]:
    row = target.step(
        open=price,
        high=price,
        low=price,
        close=price,
        volume=1.0,
    )

print(row)  # {"return": 0.3}
```

说明：`horizon=2` 的 target 需要当前点之后 2 根 K 线才能确定，因此 `step()` 返回的是延迟到未来窗口完成后才可计算的 anchor target。当前实现优先包装 stateless future effect；依赖反向调用状态的 future EMA 等不作为在线 `step()` 包装的第一批对象。

## 设计依据

- `docs/design/sigma2-20260704-overview.md`
- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`
- `pyta2/pyta2/base/indicator.py`

当前仓库中的 `pyta2` 是指向相邻仓库的软链接，只作为设计与验证参考，不应作为 sigma2 源码提交。正式环境仍应显式安装或暴露 pyta2。

## 验证

```bash
pytest -q
python -m compileall -q sigma2 tests
```
