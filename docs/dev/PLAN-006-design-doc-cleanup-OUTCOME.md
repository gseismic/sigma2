# PLAN-006 整理设计文档结果

更新时间：2026-07-04 16:35 CST

## 完成内容

- 将原 stable-core 设计内容整理为唯一当前设计总文档：`docs/design/sigma2-20260704-overview.md`。
- 将过时设计移动到 `docs/design/backup/`：
  - `docs/design/backup/sigma2-20260704-roadmap.md`
  - `docs/design/backup/sigma2-20260704-signal-core.md`
  - `docs/design/backup/sigma2-20260704-system-design.md`
- 在每份备份设计文档开头加入历史备份说明，明确不作为当前实现依据。
- 在总文档中补充应用层、`DataSchema`、`FamilyRegistry` 和 minbt adapter 边界，避免只保留 core 而丢失总体设计上下文。
- 更新 README、交接文档和计划索引，使当前引用统一指向 `docs/design/sigma2-20260704-overview.md`。

## 结论

后续实现和设计评审只应读取 `docs/design/sigma2-20260704-overview.md` 作为当前设计依据。`docs/design/backup/` 中的文档仅用于追溯讨论历史。
