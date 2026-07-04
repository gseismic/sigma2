# sigma2 交接文档

更新时间：2026-07-04 12:11 CST

## 项目背景

sigma2 是计划中的金融时间序列标准信号计算库。它可以组合 pyta2 rolling 指标，但不应只是 pyta2 封装；核心应是类似 `pyta2.base.rIndicator` 的通用 `rSignal`，并通过数据类型专属子类提供标准输入输出、自定义信号、组合信号、rolling/batch 一致执行和 ML 矩阵输出能力。K 线只是第一种数据类型，未来还要扩展 orderbook、trades 等。

当前项目仍处于初始化规划阶段，尚未实现 Python 包代码。

## 当前仓库状态

- 当前仓库目录：`/Users/mac/pai-studio-fin/library/sigma2`
- 当前分支：`main`
- 已跟踪文件原本只有 `.gitignore` 和 `AGENTS.md`。
- `pyta2` 是指向 `../pyta2` 的软链接，当前为未跟踪状态，只作为本次规划参考。
- 本次新增文档均位于仓库自身目录，不依赖提交 `pyta2` 软链接。

## 本次完成工作

- 阅读 `pyta2/docs/design/pyta2-sigma-20260627-v3.md`。
- 抽查 pyta2 实现，确认 `rIndicator` 已提供 `output_keys`、`schema`、`required_window`、`meta_info`。
- 确认 `rATR`、`rMACD`、`rSMA` 的真实输入签名、输出和窗口形态。
- 创建 `README.md`。
- 创建 `docs/design/sigma2-20260704-roadmap.md`。
- 创建 `docs/dev/PLAN-001-sigma2-roadmap.md`。
- 创建 `docs/dev/PLAN-001-sigma2-roadmap-OUTCOME.md`。
- 创建 `docs/dev/INDEX.md`。
- 根据用户反馈新增 `docs/design/sigma2-20260704-signal-core.md`。
- 新增 `docs/dev/PLAN-002-signal-core-revision.md` 和结果文件。
- 更新 README、roadmap、INDEX 和交接文档，修正核心方向。
- 根据进一步反馈补充 data-kind 分层：`rSignal` 不锁死 K 线输入，K 线由 `rKlineSignal` 承担，未来 orderbook/trades 用对应子类扩展。

## 核心结论

- sigma2 第一核心抽象应是通用 `rSignal`，不是 `FeatureSpec`。
- `rSignal` 应尽量保持与 `pyta2.base.rIndicator` 一致的生命周期、schema、输出缓存和元信息，但不固定具体行情输入。
- K 线由 `rKlineSignal` 表达，rolling 输入固定为 `opens, highs, lows, closes, volumes`。
- K 线单点实时更新输入固定为 `open, high, low, close, volume`。
- orderbook/trades 等未来数据类型通过 `rOrderBookSignal`、`rTradeSignal` 等 data-kind 子类扩展。
- 输出应通过 schema 标准化为 dict。
- pyta2 指标通过 `rPyta2Signal` 适配为 sigma2 标准信号。
- 自定义信号和组合信号必须是一等能力。
- `FeatureSpec` 可后续作为声明式配置或矩阵输出层，不能作为第一公共 API。
- batch 默认必须 replay rolling engine，不能先拼接 pyta2 batch 函数。
- pyta2 当前不允许 `buffer_size=0`，sigma2 adapter 初期应使用 `buffer_size=1`。

## 重要文档

- `README.md`
- `docs/design/sigma2-20260704-roadmap.md`
- `docs/design/sigma2-20260704-signal-core.md`
- `docs/dev/PLAN-001-sigma2-roadmap.md`
- `docs/dev/PLAN-002-signal-core-revision.md`
- `docs/dev/INDEX.md`
- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`

## 建议下一步

优先实施 `docs/dev/PLAN-002-signal-core-revision.md` 中修正后的阶段：

1. 创建 Python 包骨架和测试框架。
2. 实现通用 `rSignal` 基类。
3. 实现 `rKlineSignal` 和标准 OHLCV buffer。
4. 实现 K 线自定义信号测试，如 return、gap。
5. 实现 `rPyta2Signal`，用 rSMA、rATR、rMACD 做适配测试。
6. 实现最小 `SignalEngine.update()` 和 `SignalEngine.batch()`，内部按 data-kind 路由输入。

不要先做大量 DSL、复杂 `SignalGraph`、orderbook 字段设计或 batch 性能优化。
