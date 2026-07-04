# sigma2 交接文档

更新时间：2026-07-04 17:07 CST

## 项目背景

sigma2 是计划中的量化 rolling signal 与 ML 特征生成库。当前最稳定的核心定位已经从 `FeatureSet` 应用门面修正为类似 `pyta2.base.rIndicator` 的轻量继承式信号体系：用户应能直接继承 `rSignal` / family 子类定义信号，并把这些信号复用于 ML batch、回测、实盘、minbt adapter 或其它应用层。

当前项目仍处于初始化规划阶段，尚未实现 Python 包代码。

## 当前仓库状态

- 当前仓库目录：`/Users/mac/pai-studio-fin/library/sigma2`
- 当前分支：`main`
- 当前唯一有效设计文档：`docs/design/sigma2-20260704-overview.md`
- `docs/design/backup/` 中的文档仅用于历史追溯，不作为当前实现依据。
- `pyta2` 是指向 `../pyta2` 的软链接，当前为未跟踪状态，只作为规划参考。
- `minbt` 是本地软链接，当前为未跟踪状态，只作为边界参考。
- `AGENTS.md` 有用户侧修改，后续工作不要擅自回退。

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
- 根据最新设计讨论，废弃 `rolling()` / `update()` 作为 sigma2 core 稳定入口，改为 `step()` 唯一公共状态推进入口。
- 更新 `docs/design/sigma2-20260704-overview.md`：新增 `rKlineWindowSignal`，明确 `forward()` 是计算 hook，窗口维护由内部 `_step_forward()` 处理，`window` 不等于默认输入历史，orderbook/trade 默认不维护历史窗口。
- 新增 `docs/dev/PLAN-007-step-core-api.md` 和结果文件。

## 核心结论

- sigma2 core 不是 `FeatureSet`，而是 `rSignal` / family 子类体系。
- `rSignal` 中 `r` 表示 rolling signal 的有状态对象，但 sigma2 core 的唯一公共入库入口是 `step()`，不是 `rolling()`。
- `rSignal` 的 `window`、`schema`、`output_keys`、`required_window`、`forward()`、`reset()`、`reset_extras()`、`outputs`、`g_index`、`return_dict`、`make_dict_output()`、`meta_info` 应尽可能与 `rIndicator` 保持同一心智模型。
- `step()` 调用一次表示输入流推进一个新观测点或事件，并且是唯一会推进 `g_index`、调用 `forward()`、写入输出缓存、处理 `return_dict` 的公共方法。
- `forward()` 是子类实现计算逻辑的 hook，类似神经网络 forward；直接调用不进入 core 生命周期。
- `rolling()` 不属于 sigma2 通用 core API；pyta2 adapter 可以在内部调用 pyta2 的 `rolling()`。
- `update()` 不属于 sigma2 core API。同周期 K 线修正、未完成 K 线 preview、盘口 delta 应由 adapter、stream builder、preview runner 或独立 delta family 处理。
- `window` 表示产生有效输出所需最少 step 数，不表示 core 默认维护原始输入历史。
- `rKlineSignal` 是第一批冻结 family 子类：`step(open, high, low, close, volume)`，不默认维护 OHLCV 历史窗口。
- `rKlineWindowSignal` 是 K 线窗口型基类：在 `step()` 调用链的内部 `_step_forward()` 中维护 `opens/highs/lows/closes/volumes`，给 SMA、ATR、MACD、pyta2 adapter 等使用。
- Signal family 由输入类型决定，稳定公共命名采用 `family`；旧文档中的 `data_kind` 仅作为内部兼容别名或历史术语。
- 输入类型仍是二次开发扩展轴：`InputType / MarketDataKind -> SignalFamily -> rSignal subclass`。
- 新增数据类型应通过新的 family 子类和后续应用层 registry 加入，不应污染已有 family。
- orderbook/trade 已预留扩展原则和候选契约，但在真实信号和 contract tests 不足前不应过早冻结复杂 L2/L3 细节；默认不维护输入历史窗口。
- minbt 只作为 adapter，sigma2 核心命名使用 `kline/orderbook/trade/news`。
- `FeatureSet`、`OnlineFeatureState`、`rSignal` 不能出现 `minbt` 等外部框架名。
- pyta2 指标通过适配层接入 `rKlineWindowSignal`，对外只暴露 `step()`，sigma2 不重复维护 pyta2 指标定义。

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
- `docs/dev/PLAN-007-step-core-api.md`
- `docs/dev/INDEX.md`
- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`

## 建议下一步

优先按 `docs/design/sigma2-20260704-overview.md` 实施最小稳定核心。`docs/design/backup/` 内文档仅作历史追溯，不作为当前设计依据。

1. 创建 Python 包骨架和测试框架。
2. 实现 `rSignal`，包含 `step()`、`forward()`、schema 输出、`reset()`、`outputs`、`latest`、`required_window` 和 `meta_info`。
3. 实现 `rKlineSignal`，固定单根 K 线 `step(open, high, low, close, volume)` 输入，不默认维护历史窗口。
4. 实现 `rKlineWindowSignal`，内部维护 OHLCV 历史窗口，子类仍实现窗口序列版 `forward()`。
5. 实现 `rReturn`、`rGap` 两个纯 sigma2 K 线信号。
6. 写 core contract tests，锁住 `step()` 生命周期、`forward()` 非 core 生命周期语义、输出、warmup、reset 和 window opt-in 行为。
7. 实现 `rPyta2Signal`，内部适配 pyta2 的 `rolling()`，对外只暴露 `step()`。
8. 实现最小 `SignalEngine`，作为 core 消费者。
9. core 稳定后再实现 `FeatureSet`、DataFrame batch、minbt adapter、orderbook/trade family 和 ML matrix builder。

不要先做复杂 DAG、batch 向量化优化、minbt 深度集成或同周期 update/rollback；这些都应在 core `step()` 契约稳定后消费 core。
