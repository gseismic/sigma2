# PLAN-049：实施结果

- 完成时间：2026-10-30 16:33 CST
- 计划：`docs/dev/PLAN-049-fix-review-findings.md`
- 设计：`docs/design/review-fixes-20261030-overview.md`

## 结果

- `n_backward`、`n_forward` 和 `buffer_size` 改为只读属性，避免运行中修改元信息而不更新计算窗口或缓存。
- 在线缓存与批量表统一使用 schema 存储规则：可空或多维输出使用 object，普通标量保留原 dtype。批量重放在消费数据前检查输出格式与依赖。
- 将 pyta2 依赖固定到 `65071a84099c30a4d9476c327232da7c057b2caa`；对照该提交源码，`rROC` 和 `rSortedAt` 已使用当前 `n_backward` 构造接口。
- 盘口价差从全部档位提取最高买价和最低卖价，不依赖档位顺序；任一侧为空仍返回 NaN。
- 固定权重保留原始正权重，市值模式使用当期市值。普通贡献使用浮点和 `fsum`；权重比例或贡献过小时使用 `Fraction` 累计，避免在求和前丢失可表示的极小结果。`weights` 属性返回原始正权重副本。
- 更新 README、设计和使用说明；pyta2 桥接示例展示数组输出与 ROC，盘口示例展示未排序档位。

## 审阅与检查

- 静态审阅配置只读性、schema 存储类型、重放前错误处理、固定和动态权重归一化、极小贡献累计及缺失数据分支。
- `ruff check sigma2 examples`、`ruff format --check sigma2 examples` 和 `git diff --check` 通过。
- 按用户此前要求，未编写或运行测试，也未运行示例。已有测试仍引用旧接口，尚未迁移。
