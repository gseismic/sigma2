# 计划执行索引

更新时间：2026-07-04 16:35 CST

## 历史说明

本索引创建时，仓库中不存在既有 `docs/dev/INDEX.md`、计划文件或结果文件。更早历史只可从 git 提交记录追溯，当前未发现可迁移的历史计划文档。

## 记录

| 更新时间 | 计划文件 | 结果文件 | 摘要 |
| --- | --- | --- | --- |
| 2026-07-04 10:38 CST | `PLAN-001-sigma2-roadmap.md` | `PLAN-001-sigma2-roadmap-OUTCOME.md` | 依据 `pyta2/docs/design/pyta2-sigma-20260627-v3.md` 完成 sigma2 初始化规划，明确项目定位、API 方案、内部架构、实施阶段和下一步优先级。 |
| 2026-07-04 12:11 CST | `PLAN-002-signal-core-revision.md` | `PLAN-002-signal-core-revision-OUTCOME.md` | 根据用户反馈修正核心方向：sigma2 不是 pyta2 薄封装，应先实现类似 `rIndicator` 的通用 `rSignal`、K 线专属 `rKlineSignal`、标准输出、自定义信号和 pyta2 适配信号，并保留 orderbook/trades 的 data-kind 扩展口。 |
| 2026-07-04 13:29 CST | `PLAN-003-system-design.md` | `PLAN-003-system-design-OUTCOME.md` | 从 ML 量化策略开发主场景出发，形成系统设计稿：用户主入口为 `FeatureSet.batch(data)` 和 `FeatureSet.online()`，内部输入对象不进入普通用户主路径，`rSignal` 明确为 rolling 内核，minbt 仅作为 adapter。 |
| 2026-07-04 15:50 CST | `PLAN-004-family-registry-design.md` | `PLAN-004-family-registry-design-OUTCOME.md` | 将输入类型决定 family 升级为系统扩展原则，增加 `FamilyRegistry` 设计，明确新增数据类型不改核心类，并修正 minbt 适配示例避免污染 core API。 |
| 2026-07-04 16:31 CST | `PLAN-005-stable-core-api.md` | `PLAN-005-stable-core-api-OUTCOME.md` | 根据用户进一步反馈修正设计优先级：sigma2 core 应像 `pyta2.base.rIndicator` 一样轻量，稳定对象是 `rSignal` / `rKlineSignal` 继承式信号体系；`FeatureSet`、DataFrame batch、minbt adapter 下调为应用层或适配层；`rSignal` 的概念、命名、生命周期和默认行为应尽可能与 `rIndicator` 保持一致。 |
| 2026-07-04 16:35 CST | `PLAN-006-design-doc-cleanup.md` | `PLAN-006-design-doc-cleanup-OUTCOME.md` | 整理 `docs/design`，只保留 `sigma2-20260704-overview.md` 作为当前总设计文档；过时设计移动到 `docs/design/backup/` 并标注历史备份，防止误读。 |

## 当前设计文档规则

- `docs/design/sigma2-20260704-overview.md` 是唯一当前设计依据。
- `docs/design/backup/` 中的文档仅用于历史追溯，不作为实现依据。
