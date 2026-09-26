# PLAN-025：直接调用 pyta2 子指标

创建时间：2026-09-26 15:43 CST
更新时间：2026-09-26 16:02 CST
状态：已实施，结果见 `PLAN-025-direct-pyta2-calls-OUTCOME.md`

## 目标

依据 [直接调用设计](../design/direct-pyta2-20260926-overview.md)，删除 `Pyta2Component` 与 `rSignal.apply_component()`，让持有 pyta2 子指标的 Signal 直接调用其 `rolling()/update_last()/reset()`，保持数值、修订、批量与输出身份行为。

## 实施步骤

1. 迁移两级 MA V2、单指标 K 线模板、通用 pyta2 Signal 和盘口组合测试到直接调用；保留 V2 生命周期外调用防护及单指标历史 `forward()` 行为。
2. 删除适配类、core 分派方法及公开导出；更新只验证旧接口的测试，以直接调用后的修订与错误行为为准。
3. 因公开接口移除，将包版本与 README 推进至 0.5.0；更新扩展指南和当前设计文档入口，旧设计/计划结果保留历史原貌。
4. 运行相关测试、全套测试、Ruff、语法检查与示例；审阅差异并修复问题。
5. 生成本计划的 OUTCOME，追加 `docs/dev/INDEX.md` 对应记录；按项目约定提交并立即推送。

## 完成标准

- 当前源码、公开导出和指导文档不再要求 `Pyta2Component` 或 `apply_component()`。
- 八种 MA、通用 pyta2 桥接、盘口组合和非 pyta2 子对象的末根修订与 replay 等价；V2 生命周期外 `forward()` 不推进子指标。
- 只提交本计划相关文件，不包含本地未跟踪软链接。
