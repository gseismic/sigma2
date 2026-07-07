# PLAN-010 core-only 包结构迁移

更新时间：2026-07-07 12:01 CST

## 背景

当前设计已经确认 sigma2 的源码结构应以信号为中心：根目录直接出现 `kline/`、`orderbook/`、`trade/` 等输入数据类型分类，每个具体信号一个文件。上一版设计仍同时保留 `base/` 和 `core/`，用户反馈这会让基础层语义重复，应二选一，保留 `core` 更清晰。

当前代码仍是旧结构：

- `sigma2/base/`
- `sigma2/families/`
- `sigma2/signals/`
- `sigma2/adapters/`

这与当前设计不一致。

## 目标

1. 只保留 `core/` 作为非信号核心目录，不再保留 `base/`。
2. 将 family 基类迁移到 `sigma2/core/`。
3. 将具体信号迁移到根级 family 包，并保证每个信号一个文件。
4. 将 pyta2 通用信号基类迁移到 `sigma2/core/pyta2.py`。
5. 将 pyta2 导入兼容、resolver、registry 等无状态辅助迁移到 `sigma2/utils/pyta2.py`。
6. 更新测试，覆盖新导入路径。
7. 更新当前设计、README、交接文档和计划索引。

## 非目标

- 不实现 `SignalEngine` / `FeatureSet`。
- 不实现 minbt adapter。
- 不扩展 pyta2 indicator catalog。
- 不保留旧 `base/`、`families/`、`signals/`、`adapters/` 的兼容导入层。

## 目标结构

```text
sigma2/
  __init__.py
  core/
    __init__.py
    signal.py
    kline.py
    orderbook.py
    trade.py
    pyta2.py
  utils/
    __init__.py
    pyta2.py
  kline/
    __init__.py
    gap.py
    return_.py
    sma.py
    pyta2/
      __init__.py
      sma.py
  orderbook/
    __init__.py
    book_spread.py
  trade/
    __init__.py
    trade_signed_volume.py
```

## 公共导入

必须可用：

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

必须不可作为当前公共路径依赖：

```python
sigma2.base
sigma2.families
sigma2.signals
sigma2.adapters
```

## 验收

- `pytest -q` 通过。
- `python -m compileall -q sigma2 tests` 通过。
- 新导入路径 contract tests 通过。
- 当前设计文档不再把 `base/` 作为目标结构。
