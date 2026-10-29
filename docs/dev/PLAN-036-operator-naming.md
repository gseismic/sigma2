# PLAN-036：明确算子接口和快照命名

- 创建时间：2026-10-30 05:38 CST
- 依据：用户对 `rOperator.step`、`forward` 和 `_before_last` 的审阅。
- 状态：已实施并静态审阅；未编写或运行测试。实施时按用户要求未提交，用户于 2026-10-30 随后要求提交。

## 步骤

1. 更新 core 设计说明：明确 `step`、`forward` 的职责和未确认观测前的快照含义。
2. 将 `_before_last` 重命名为 `_state_before_pending`，补充必要注释；抽象 `step` 被误调用时抛出 `NotImplementedError`。
3. 静态审阅修改，记录结果并更新计划历史；按照用户要求不编写或运行测试，不提交或推送。
