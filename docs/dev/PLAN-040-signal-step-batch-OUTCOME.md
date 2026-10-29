# PLAN-040：实施结果

- 完成时间：2026-10-30 06:11 CST
- 计划：`docs/dev/PLAN-040-signal-step-batch.md`
- 设计：`docs/design/signal-step-batch-20261030-overview.md`

## 结果

- 在 core 增加 `forward_step_apply`，借鉴 pyta2 使用 `VectorTable` 和 `get_outputs`，逐条调用 Signal 的 `step`；不导入 K 线等数据模块。
- 根据 Signal 的观测索引追加或更新结果；未声明 schema 的输出按 object 类型建立列，避免用首个数值推断后续类型。
- 恢复 `KlineMA`、`KlineMACD` 和对应导出；批量结果默认按 schema 字段命名，并可选 pyta2 支持的输出格式和算子元信息。
- 更新报错的 `examples/01_kline_batch.py`，使用固定 K 线字段字典和当前输出字段；更新 README 与设计说明。

## 审阅与检查

- 静态审阅了 pyta2 固定版本的 `VectorTable` 和 `get_outputs`、core 的未结束观测重算及 MA、MACD 的 schema 和导出。
- `ruff check`、`ruff format --check` 和 `git diff --check` 通过。按用户此前要求，未编写或运行测试，也未执行示例；结果与实时更新行为仍需后续运行验证。
- 本轮只处理 MA、MACD 的批量入口和标量 Signal 输出；旧 batch、其他指标和 Outcome 尚未迁移。输入不兼容旧 `KlineBar`、额外字段或字段映射，需按 `step` 签名整理。
- 实施时改动未提交并保留供审阅，用户随后要求提交。
