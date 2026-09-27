# PLAN-026：Signal 单向逐条运行

创建时间：2026-09-27 12:17 CST

更新时间：2026-09-27 12:23 CST
状态：已实施，结果见 `PLAN-026-rolling-only-signal-OUTCOME.md`

## 目标

依据 [单向逐条运行设计](../design/sigma2-20260927-rolling-only.md)，使 sigma2 与当前只提供 `rolling()` 的 pyta2 配合，移除 Signal 的 `update_last()` 能力。旧设计整体归档到 `docs/backup/v2/`。

## 实施步骤

1. 将原 `docs/design/` 全部内容移动到 `docs/backup/v2/`，新建当前设计文档，并更新 README 与使用指南的设计入口。
2. 删除 core 及各 family 的 `update_last()`、检查点/恢复、能力标志与元信息；保留 `step()`、`reset()`、失败锁定、窗口及 batch replay。
3. 使 pyta2 桥接、单指标因子和两级均值组合只调用子指标 `rolling()`；清理内置 Signal 与 target 的旧修订声明。
4. 更新示例和测试：删除只验证修订的测试，用单向推进、重放、warmup、父子索引同步与失败恢复测试覆盖真实风险。
5. 运行测试、Ruff、语法检查和示例；审阅差异并修复问题。生成 OUTCOME，追加 INDEX，按仓库规范提交并立即推送。

## 完成标准

- `rSignal`、各 family 与内置 Signal 均无 `update_last()`，源码和当前指导不调用 pyta2 的旧方法。
- batch 与逐条计算、窗口预热、`reset()` 重放及错误状态行为通过验证。
- 旧设计文件均位于 `docs/backup/v2/`；只提交本计划相关文件，不包含未跟踪软链接。
