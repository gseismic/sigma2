# sigma2

sigma2 是面向金融时间序列和机器学习特征工程的信号计算库。它不是 pyta2 的薄封装，也不是以 `FeatureSet` 为中心的应用框架；它的稳定核心是一套类似 `pyta2.base.rIndicator` 的轻量有状态 signal 基类体系。用户应能直接继承 `rSignal` / family 子类定义信号，应用层再把这些信号用于 batch、online、minbt 或 ML 特征矩阵。

## 项目定位

- `sigma2` 的通用核心是 `rSignal`，总体结构应尽量接近 `pyta2.base.rIndicator` 的状态、schema、输出缓存和元信息心智。
- `rSignal.step()` 是唯一公共状态推进入口，调用一次表示输入流推进一个新观测点或事件。
- `rSignal.forward()` 是子类计算 hook，类似神经网络 forward；直接调用不推进 core 生命周期状态、不写输出缓存、不处理 `return_dict`。
- `rSignal` 不提供通用 `rolling()` 或 `update()`；历史窗口和同周期修正不是 core 默认能力。
- `window` 表示产生有效输出所需最少 step 数，不等于 core 必须保存原始输入历史。
- `rKlineSignal` 标准化单根已确定 K 线输入：`open, high, low, close, volume`。
- `rKlineWindowSignal` 为需要 OHLCV 历史序列的 K 线信号 opt-in 维护窗口。
- 未来可扩展 `rOrderBookSignal`、`rTradeSignal` 等数据类型专属信号，各自定义标准 `step()` 输入契约。
- `sigma2` 支持自定义信号、组合信号，以及把 pyta2 rolling 指标适配为对外 `step()` 的信号。
- `pyta2` 是可复用指标内核和元信息来源，但不是 sigma2 的唯一抽象中心。
- `FeatureSet`、DataFrame batch、online state 和 minbt adapter 属于应用层或适配层，应消费 core，不定义 core。
- 样本裁剪、标签生成、训练集切分和策略回测不属于 sigma2 核心范围。

## 抽象分层

稳定核心：

- `rSignal`：sigma2 通用信号基类，提供 `window`、`schema`、`output_keys`、`required_window`、`step()`、`forward()`、`reset()`、`reset_extras()`、`outputs`、`latest`、`g_index`、`return_dict` 和 `meta_info`。
- `rKlineSignal`：K 线信号基类，固定单根 K 线 `step()` 输入契约。
- `rKlineWindowSignal`：K 线窗口型信号基类，内部维护 OHLCV 历史序列，给 SMA、ATR、MACD、pyta2 adapter 等使用。

上层能力：

- `rPyta2Signal`：把 pyta2 rolling 指标适配为标准 K 线窗口型信号，对外只暴露 `step()`。
- `rCompositeSignal`：组合多个 pyta2 指标、sigma2 信号或自定义逻辑，输出新的标准信号。
- `SignalGraph`：组织多个信号之间的依赖、数据类型、拓扑排序和 warmup 传播。
- `SignalEngine`：按数据类型路由输入，并用同一套执行逻辑支持在线 `step()` 和历史 `batch()` replay。
- `FeatureSet`：应用层便利门面，用标准信号对象生成 DataFrame 或 ML 矩阵，不属于 core。
- DSL：提供 `SMA()`、`ATR()`、`MACD()` 等便捷构造器，但最终返回标准信号对象。

## 同周期更新

K 线未完成周期更新、盘口 delta、实盘 preview 等场景真实存在，但不进入 `rSignal` core。它们应由 adapter、stream builder 或 preview runner 处理；正式信号状态只通过 `step()` 追加已确定的新观测点。

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

本库处于初始化规划阶段，尚未实现 Python 包代码。当前高优先级工作是按 `docs/design/sigma2-20260704-overview.md` 先完成最小可验证核心：通用 `rSignal.step()`、K 线专属 `rKlineSignal`、窗口型 `rKlineWindowSignal`、基础 K 线信号和 core contract tests。`FeatureSet`、DataFrame batch、minbt adapter 应在 core 稳定后作为应用层继续实现。
