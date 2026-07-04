# PLAN-003：形成 sigma2 系统设计文档

更新时间：2026-07-04 13:29 CST

## 背景

用户要求从真实使用场景出发，形成一份可查看的系统设计文档。最新共识：

- sigma2 的核心场景是机器学习方法开发量化交易策略。
- 普通用户不应介入 `KlineInput` 等内部输入对象。
- 用户主路径应是 `FeatureSet.batch(data)` 和 `FeatureSet.online()`。
- `rSignal` 中 `r` 表示 rolling，区别于 batch 计算。
- minbt 是适配目标，不应污染 sigma2 内部命名。

## 本计划目标

- 新增系统设计文档，沉淀当前推荐架构。
- 明确用户接口、内部接口、signal family、batch/online、pyta2/minbt 关系。
- 更新计划索引和交接文档，便于后续接续实现。

## 范围

包含：

- 新增 `docs/design/sigma2-20260704-system-design.md`。该设计后续已移入 `docs/design/backup/sigma2-20260704-system-design.md`。
- 新增本计划结果文件。
- 更新 `docs/dev/INDEX.md`。
- 更新 `docs/HANDOFF.md`。

不包含：

- 实现 Python 代码。
- 修改 minbt 或 pyta2。
- 提交未跟踪软链接。
- 处理既有未提交的 `AGENTS.md` 修改。

## 验收标准

- 文档明确 ML 特征生成是主场景。
- 文档明确普通用户不需要手写内部输入对象。
- 文档明确 `FeatureSet.batch(data)` 是用户主入口。
- 文档明确 `rSignal` 是 rolling 内核，不是 batch 主接口。
- 文档明确 signal family 由输入类型决定，单 symbol 与多 symbol 分开。
- 文档明确 minbt 只作为 adapter。
