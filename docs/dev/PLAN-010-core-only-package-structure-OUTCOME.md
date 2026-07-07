# PLAN-010 执行结果

更新时间：2026-07-07 12:01 CST

## 结果摘要

已完成 core-only 包结构迁移：

- 删除旧公共结构源码文件：`base/`、`families/`、`signals/`、`adapters/`、`_pyta2.py`。
- 新增 `sigma2/core/`，承载 `rSignal`、family 基类和 `rPyta2Signal`。
- 新增根级信号分类包：`sigma2/kline/`、`sigma2/orderbook/`、`sigma2/trade/`。
- 将具体信号拆为单文件：
  - `kline/return_.py`
  - `kline/gap.py`
  - `kline/sma.py`
  - `kline/pyta2/sma.py`
  - `orderbook/book_spread.py`
  - `trade/trade_signed_volume.py`
- 新增 `sigma2/utils/pyta2.py`，承载 pyta2 导入兼容、resolver 和 registry。
- 更新顶层 `sigma2.__init__`，继续 re-export 常用 core 类和信号。
- 更新 tests，覆盖新导入路径。
- 更新 README、交接文档和当前总设计文档。

## 当前公共导入

```python
from sigma2 import rSignal, rSMA, rPyta2SMA
from sigma2.core import rSignal, rKlineSignal, rPyta2Signal
from sigma2.kline import rReturn, rGap, rSMA
from sigma2.kline.sma import rSMA
from sigma2.kline.pyta2 import rPyta2SMA
from sigma2.orderbook import rBookSpread
from sigma2.trade import rTradeSignedVolume
from sigma2.utils.pyta2 import resolve_pyta2_indicator
```

## 验证

已执行：

```bash
pytest -q
python -m compileall -q sigma2 tests
```

结果：

- `30 passed`
- `compileall` 通过，无输出

导入路径验证通过：

- `from sigma2 import rSMA`
- `from sigma2.kline import rSMA`
- `from sigma2.kline.sma import rSMA`
- `from sigma2.orderbook import rBookSpread`
- `from sigma2.trade import rTradeSignedVolume`
- `from sigma2.core import rKlineSignal, rPyta2Signal`
- `from sigma2.utils.pyta2 import resolve_pyta2_indicator`

旧路径验证为不可用：

- `sigma2.base`
- `sigma2.families`
- `sigma2.signals`
- `sigma2.adapters`

## 后续事项

- 实现最小 `SignalEngine`。
- 实现应用层 `FeatureSet` / batch replay。
- 根据真实使用扩展更多 orderbook/trade 信号。
- 不优先做全面 pyta2 catalog 迁移。
