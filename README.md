# sigma2

sigma2 是面向金融时间序列和机器学习特征工程的信号计算库。它不是 pyta2 的薄封装，也不是以 `FeatureSet` 为中心的应用框架；它的稳定核心是一套类似 `pyta2.base.rIndicator` 的轻量 rolling signal 基类体系。用户应能直接继承 `rSignal` / `rKlineSignal` 定义信号，应用层再把这些信号用于 batch、online、minbt 或 ML 特征矩阵。

## 项目定位

- `sigma2` 的通用核心是 `rSignal`，总体结构应尽量接近 `pyta2.base.rIndicator`。
- `rSignal` 是稳定公共开发接口，概念、命名和生命周期尽可能与 `pyta2.base.rIndicator` 保持一致，规定 window、schema、输出、缓存、`g_index` 和元信息，不把输入锁死为 K 线。
- `rKlineSignal` 标准化 K 线输入：rolling 序列输入为 `opens, highs, lows, closes, volumes`。
- `rKlineSignal` 标准化单点更新：每次输入 `open, high, low, close, volume`。
- 未来可扩展 `rOrderBookSignal`、`rTradeSignal` 等数据类型专属信号，各自定义标准输入契约。
- `sigma2` 支持自定义信号、组合信号，以及把 pyta2 rolling 指标适配为信号。
- `pyta2` 是可复用指标内核和元信息来源，但不是 sigma2 的唯一抽象中心。
- `FeatureSet`、DataFrame batch、online state 和 minbt adapter 属于应用层或适配层，应消费 core，不定义 core。
- 样本裁剪、标签生成、训练集切分和策略回测不属于 sigma2 核心范围。

## 抽象分层

稳定核心：

- `rSignal`：sigma2 通用信号基类，概念上尽可能贴近 `rIndicator`，提供 `window`、`schema`、`output_keys`、`required_window`、`rolling()`、`forward()`、`reset()`、`reset_extras()`、`outputs`、`g_index`、`return_dict` 和 `meta_info`。
- `rKlineSignal`：K 线信号基类，固定 OHLCV rolling/update 输入契约。

上层能力：

- `rPyta2Signal`：把 pyta2 rolling 指标适配为标准 K 线信号，例如 SMA 绑定 `closes`，ATR 绑定 `highs/lows/closes`。
- `rCompositeSignal`：组合多个 pyta2 指标、sigma2 信号或自定义逻辑，输出新的标准信号。
- `SignalGraph`：组织多个信号之间的依赖、数据类型、拓扑排序和 warmup 传播。
- `SignalEngine`：按数据类型路由输入，并用同一套执行逻辑支持单点 `update()` 和历史 `batch()`。
- `FeatureSet`：应用层便利门面，用标准信号对象生成 DataFrame 或 ML 矩阵，不属于 core。
- DSL：提供 `SMA()`、`ATR()`、`MACD()` 等便捷构造器，但最终返回标准信号对象。

## 设计依据

主要依据本地参考文档：

- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`
- `pyta2/pyta2/base/indicator.py`
- `pyta2/pyta2/stats/atr/atr.py`
- `pyta2/pyta2/momentum/macd/macd.py`
- `pyta2/pyta2/trend/ma/sma.py`
- `docs/design/sigma2-20260704-overview.md`

当前仓库中的 `pyta2` 是指向相邻仓库的软链接，只作为设计与验证参考，不应作为 sigma2 源码提交。

## 当前状态

本库处于初始化规划阶段，尚未实现 Python 包代码。当前高优先级工作是按 `docs/design/sigma2-20260704-overview.md` 先完成最小可验证核心：通用 `rSignal`、K 线专属 `rKlineSignal`、基础 K 线信号和 core contract tests。`FeatureSet`、DataFrame batch、minbt adapter 应在 core 稳定后作为应用层继续实现。
