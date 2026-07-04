# PLAN-002：修正 sigma2 标准信号核心

更新时间：2026-07-04 12:11 CST

## 背景

用户反馈上一版规划过于像 pyta2 封装。sigma2 需要支持组合 pyta2、自定义信号，并且总体结构应与 `pyta2.base.rIndicator` 类似。主要差异应是标准化输入和标准化输出。进一步反馈明确：K 线只是其中一种数据类型，未来还要扩展 orderbook 等。

## 本计划目标

- 将 sigma2 核心从 `FeatureSpec + Pyta2Adapter` 修正为通用 `rSignal` 标准信号基类。
- 明确 `rSignal` 只规定生命周期和输出，不锁死具体数据输入。
- 明确 `rKlineSignal` 的 rolling 输入为 `opens, highs, lows, closes, volumes`。
- 明确 `rKlineSignal` 的单点更新输入为 `open, high, low, close, volume`。
- 明确未来通过 `rOrderBookSignal`、`rTradeSignal` 等 data-kind 子类扩展其它行情源。
- 明确 pyta2 只是 `rPyta2Signal` 的适配来源，不是唯一核心。
- 更新 README、设计文档、交接文档和计划索引。

## 本计划范围

包含：

- 新增 `docs/design/sigma2-20260704-signal-core.md`。
- 更新 `README.md`。
- 更新 `docs/design/sigma2-20260704-roadmap.md` 的修订状态和核心 API 方向。
- 更新 `docs/HANDOFF.md`。
- 更新 `docs/dev/INDEX.md`。
- 生成本计划结果文件。

不包含：

- 实现 Python 代码。
- 修改 pyta2。
- 提交未跟踪的 `pyta2` 软链接。

## 修正后的实施顺序

1. 实现 `rSignal` 基类，保留与 `rIndicator` 类似的生命周期、schema、输出缓存、元信息和 data-kind 元信息。
2. 实现 `rKlineSignal`，提供标准 OHLCV rolling/update 输入和内部 buffer。
3. 实现标准 schema dict 输出。
4. 实现至少两个 K 线自定义信号测试。
5. 实现 `rPyta2Signal`，接入 rSMA、rATR、rMACD。
6. 实现最小 `SignalEngine.update()` 和 `SignalEngine.batch()`，按 data-kind 路由输入。
7. 后续再实现 `SignalGraph`、共享 buffer、声明式 `SignalSpec`、orderbook/trades data-kind 和更多 DSL。

## 验收标准

- 文档明确 sigma2 不是 pyta2 薄封装。
- 文档明确 `rSignal` 是第一核心抽象。
- 文档明确 `rSignal` 不把输入锁死为 K 线。
- 文档明确 `rKlineSignal` 是第一阶段 K 线标准输入抽象。
- 文档明确 orderbook/trades 通过 data-kind 子类扩展。
- 文档明确 pyta2 指标通过 `rPyta2Signal` 适配。
- 文档明确 K 线 rolling 与单点 update 的标准输入。
- 历史索引追加 PLAN-002 记录。
