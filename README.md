# sigma2

sigma2 是面向金融时间序列和机器学习特征工程的信号计算库。它不是 pyta2 的薄封装，而是提供自己的标准信号基类、按数据类型标准化的输入契约、组合信号能力和 rolling/batch 一致执行语义；pyta2 指标是 sigma2 可以组合和适配的一类信号来源。

## 项目定位

- `sigma2` 的通用核心是 `rSignal`，总体结构应尽量接近 `pyta2.base.rIndicator`。
- `rSignal` 只规定生命周期、schema、输出、缓存和元信息，不把输入锁死为 K 线。
- `rKlineSignal` 标准化 K 线输入：rolling 序列输入为 `opens, highs, lows, closes, volumes`。
- `rKlineSignal` 标准化单点更新：每次输入 `open, high, low, close, volume`。
- 未来可扩展 `rOrderBookSignal`、`rTradeSignal` 等数据类型专属信号，各自定义标准输入契约。
- `sigma2` 支持自定义信号、组合信号，以及把 pyta2 rolling 指标适配为信号。
- `pyta2` 是可复用指标内核和元信息来源，但不是 sigma2 的唯一抽象中心。
- `sigma2` 的 batch 默认通过 rolling replay 实现，保证与实时模式一致。
- 样本裁剪、标签生成、训练集切分和策略回测不属于 sigma2 核心范围。

## 核心抽象

- `rSignal`：sigma2 通用信号基类，类似 `rIndicator`，提供 `window`、`schema`、`output_keys`、`required_window`、`rolling()`、`update()`、`outputs` 和 `meta_info`。
- `rKlineSignal`：K 线信号基类，固定 OHLCV rolling/update 输入契约。
- `rPyta2Signal`：把 pyta2 rolling 指标适配为标准 K 线信号，例如 SMA 绑定 `closes`，ATR 绑定 `highs/lows/closes`。
- `rCompositeSignal`：组合多个 pyta2 指标、sigma2 信号或自定义逻辑，输出新的标准信号。
- `SignalGraph`：组织多个信号之间的依赖、数据类型、拓扑排序和 warmup 传播。
- `SignalEngine`：按数据类型路由输入，并用同一套执行逻辑支持单点 `update()` 和历史 `batch()`。
- DSL：提供 `SMA()`、`ATR()`、`MACD()` 等便捷构造器，但最终返回标准信号对象或信号声明。

## 设计依据

主要依据本地参考文档：

- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`
- `pyta2/pyta2/base/indicator.py`
- `pyta2/pyta2/stats/atr/atr.py`
- `pyta2/pyta2/momentum/macd/macd.py`
- `pyta2/pyta2/trend/ma/sma.py`
- `docs/design/sigma2-20260704-signal-core.md`

当前仓库中的 `pyta2` 是指向相邻仓库的软链接，只作为设计与验证参考，不应作为 sigma2 源码提交。

## 当前状态

本库处于初始化规划阶段，尚未实现 Python 包代码。当前高优先级工作是按 `docs/dev/PLAN-002-signal-core-revision.md` 先完成最小可验证核心：通用 `rSignal`、K 线专属 `rKlineSignal`、`rPyta2Signal` 和基础 rolling/update 一致性，同时保留 orderbook 等数据类型扩展口。
