# PLAN-006 整理设计文档

更新时间：2026-07-04 16:35 CST

## 背景

用户要求整理 `docs/design`：过时设计要移入 `docs/design/backup` 或明确标注，只保留一份当前总文档，避免后续实现或其它 agent 误读旧结论。

## 目标

- `docs/design` 根目录只保留一份当前设计总文档。
- 旧设计移动到 `docs/design/backup`。
- 旧设计文件开头标注“历史备份，不作为当前实现依据”。
- README、HANDOFF、计划索引和当前计划结果只引用新的总文档。
- 保留历史计划记录，但明确当前实现依据。

## 范围

- 移动和标注设计文档。
- 更新当前文档引用。
- 不修改 Python 代码。
- 不修改 `AGENTS.md` 或未跟踪软链接。

## 预期产物

- `docs/design/sigma2-20260704-overview.md`
- `docs/design/backup/sigma2-20260704-roadmap.md`
- `docs/design/backup/sigma2-20260704-signal-core.md`
- `docs/design/backup/sigma2-20260704-system-design.md`
- `docs/dev/PLAN-006-design-doc-cleanup-OUTCOME.md`
- 更新 `README.md`
- 更新 `docs/HANDOFF.md`
- 更新 `docs/dev/INDEX.md`
