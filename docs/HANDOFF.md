# sigma2 交接文档

更新时间：2026-07-04 16:35 CST

## 项目背景

sigma2 是计划中的量化 rolling signal 与 ML 特征生成库。当前最稳定的核心定位已经从 `FeatureSet` 应用门面修正为类似 `pyta2.base.rIndicator` 的轻量继承式信号体系：用户应能直接继承 `rSignal` / `rKlineSignal` 定义信号，并把这些信号复用于 ML batch、回测、实盘、minbt adapter 或其它应用层。

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
- 创建 `docs/design/sigma2-20260704-roadmap.md`，后续已移入 `docs/design/backup/sigma2-20260704-roadmap.md`。
- 创建 `docs/dev/PLAN-001-sigma2-roadmap.md`。
- 创建 `docs/dev/PLAN-001-sigma2-roadmap-OUTCOME.md`。
- 创建 `docs/dev/INDEX.md`。
- 根据用户反馈新增 `docs/design/sigma2-20260704-signal-core.md`，后续已移入 `docs/design/backup/sigma2-20260704-signal-core.md`。
- 新增 `docs/dev/PLAN-002-signal-core-revision.md` 和结果文件。
- 更新 README、roadmap、INDEX 和交接文档，修正核心方向。
- 根据进一步反馈补充 data-kind 分层：`rSignal` 不锁死 K 线输入，K 线由 `rKlineSignal` 承担，未来 orderbook/trades 用对应子类扩展。
- 根据最新讨论新增 `docs/design/sigma2-20260704-system-design.md`，后续已移入 `docs/design/backup/sigma2-20260704-system-design.md`。
- 新增 `docs/dev/PLAN-003-system-design.md` 和结果文件。
- 更新计划索引和交接文档，明确 ML 主路径与内部输入对象边界。
- 根据最新讨论更新系统设计，补充输入类型驱动 family 和 `FamilyRegistry`。
- 新增 `docs/dev/PLAN-004-family-registry-design.md` 和结果文件。
- 修正 minbt 示例，禁止 `update_minbt_bars(...)` 这类外部框架方法出现在 core 对象。
- 根据最新反馈修正核心优先级：`FeatureSet` 可由应用层完成，sigma2 core 应像 `pyta2.base.rIndicator` 一样轻量。
- 新增 `docs/design/sigma2-20260704-stable-core.md`，后续已整理为 `docs/design/sigma2-20260704-overview.md`。
- 新增 `docs/dev/PLAN-005-stable-core-api.md` 和结果文件。
- 更新 README、system design、INDEX 和交接文档，明确 core-first 实施顺序。
- 根据用户补充要求，强调 `rSignal` 概念、命名、生命周期和默认行为尽可能与 `pyta2.base.rIndicator` 保持一致。
- 根据用户要求整理 `docs/design`：将唯一当前设计总文档改为 `docs/design/sigma2-20260704-overview.md`，过时设计移入 `docs/design/backup/` 并标注历史备份。
- 新增 `docs/dev/PLAN-006-design-doc-cleanup.md` 和结果文件。

## 核心结论

- sigma2 core 不是 `FeatureSet`，而是 `rSignal` / family 子类体系。
- `rSignal` 中 `r` 表示 rolling，是最稳定的公共开发接口；其 `window`、`schema`、`output_keys`、`required_window`、`rolling()`、`forward()`、`reset()`、`reset_extras()`、`outputs`、`g_index`、`return_dict`、`make_dict_output()`、`meta_info` 应尽可能与 `rIndicator` 保持同一心智模型。
- `rKlineSignal` 是第一批冻结 family 子类：rolling 输入 `opens, highs, lows, closes, volumes`，update 输入 `open, high, low, close, volume`。
- `rolling()` 是与 `rIndicator` 对齐的主生命周期入口；`update()` 在 base 层最多是 `rolling()` 的兼容别名，在 family 子类才表达单点行情输入，且应委托 `rolling()` 的生命周期。
- `FeatureSet.batch(data)`、`FeatureSet.online()`、DataFrame batch、online state 是应用层能力，应消费 core，不定义 core。
- Signal family 由输入类型决定，稳定公共命名采用 `family`；旧文档中的 `data_kind` 仅作为内部兼容别名或历史术语。
- 输入类型仍是二次开发扩展轴：`InputType / MarketDataKind -> SignalFamily -> rSignal subclass`。
- 新增数据类型应通过新的 family 子类和后续应用层 registry 加入，不应污染已有 family。
- orderbook/trade 已预留扩展原则和候选契约，但在真实信号和 contract tests 不足前不应过早冻结复杂 L2/L3 细节。
- minbt 只作为 adapter，sigma2 核心命名使用 `kline/orderbook/trade/news`。
- `FeatureSet`、`OnlineFeatureState`、`rSignal` 不能出现 `minbt` 等外部框架名。
- pyta2 指标通过适配层接入 kline rolling 信号，sigma2 不重复维护 pyta2 指标定义。

## 重要文档

- `README.md`
- `docs/design/sigma2-20260704-overview.md`
- `docs/design/backup/sigma2-20260704-roadmap.md`
- `docs/design/backup/sigma2-20260704-signal-core.md`
- `docs/design/backup/sigma2-20260704-system-design.md`
- `docs/dev/PLAN-001-sigma2-roadmap.md`
- `docs/dev/PLAN-002-signal-core-revision.md`
- `docs/dev/PLAN-003-system-design.md`
- `docs/dev/PLAN-004-family-registry-design.md`
- `docs/dev/PLAN-005-stable-core-api.md`
- `docs/dev/PLAN-006-design-doc-cleanup.md`
- `docs/dev/INDEX.md`
- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`

## 建议下一步

优先按 `docs/design/sigma2-20260704-overview.md` 实施最小稳定核心。`docs/design/backup/` 内文档仅作历史追溯，不作为当前设计依据。

1. 创建 Python 包骨架和测试框架。
2. 实现 `rSignal`，包含 schema 输出、`rolling()`、`reset()`、`outputs`、`required_window` 和 `meta_info`；`update()` 在 base 层最多作为 `rolling()` 兼容别名。
3. 实现 `rKlineSignal`，包含 OHLCV buffer 和标准 K 线 rolling/update 输入。
4. 实现 `rReturn`、`rGap` 两个纯 sigma2 K 线信号。
5. 写 core contract tests，锁住继承、输出、warmup、reset 和 update/rolling 一致性。
6. 实现 `rPyta2Signal`，再接入 rSMA、rATR、rMACD。
7. 实现最小 `SignalEngine`，作为 core 消费者。
8. core 稳定后再实现 `FeatureSet`、DataFrame batch、minbt adapter、orderbook/trade family 和 ML matrix builder。

不要先做 `FeatureSet`、复杂 DAG、batch 向量化优化或 minbt 深度集成；这些都应在 core 稳定后消费 core。
