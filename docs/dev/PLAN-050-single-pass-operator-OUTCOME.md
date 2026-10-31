# PLAN-050：实施结果

- 完成时间：2026-10-31 14:25 CST
- 计划：`docs/dev/PLAN-050-single-pass-operator.md`
- 设计：`docs/design/operator-single-pass-20261031-overview.md`

## 结果

- `rOperator.step()` 统一推进索引、调用 `forward()`、检查输出和追加缓存；计算前设置失败标记，全部成功后解除，失败后必须新建实例并重放。
- 移除末根重算、初始与未确认状态快照、观测标识检查、`reset()` 和 `_state` 容器。单 K 线入口不再接收 `is_closed`；同一时间的重复输入仍按不同观测推进。
- K 线、Bundle、盘口和成交入口使用 `super().step()`；指标、Outcome、桥接及示例使用普通实例属性保存子指标和计算窗口。
- 批量重放每条成功输入追加一行，Outcome 继续按 `result_index` 回填锚点；保留已有实例续放、schema 类型和缺失值语义。
- 更新 README、使用指南、示例和历史设计文档的当前契约指引。

## 审阅与检查

- 静态核对各数据类型的继承调用和输入签名，检查 RSI、其他指标、价格窗口、未来结果和 Bundle 的子对象及窗口长度；`g_index` 在 `forward()` 前推进，ATR 边界的绝对位置表达保留。
- 静态核对失败锁定涵盖计算、输出字段检查和在线缓存写入；入口提前拒绝的输入不推进算子。失败实例的索引、缓存和子对象不保证可用。
- 静态核对批量从已有实例继续时的首个索引与 Outcome 锚点回填，保留尾部未成熟位置及批量整理异常不撤销既有推进的语义。
- `ruff check sigma2 examples`、`ruff format --check sigma2 examples`、`git diff --check` 通过。
- 按用户此前要求，未编写或运行测试，也未运行示例；运行时行为尚未验证，现有测试仍使用旧接口。
