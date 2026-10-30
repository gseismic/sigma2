# PLAN-047：实施结果

- 完成时间：2026-10-30 15:20 CST
- 计划：`docs/dev/PLAN-047-return-rank-stable-sort.md`
- 设计：`docs/design/kline-bundle-return-rank-20261030-overview.md`

## 结果

- 收益率排名使用稳定排序和一次 `for` 循环分配整数名次；相同收益率按当前 Bundle 的输入顺序排列，不再取平均名次。
- 在 `rKlineBundleReturnRank` 类文档中说明收益率公式、截面步数、排序方式、缺失条件和输出格式。
- 同步更新 README 中的排名示例、设计文档、使用指南和独立示例注释。

## 审阅与检查

- 静态审阅升序与降序的稳定排序、名次从 1 开始、无效收益率保留 NaN，以及输出仍包含当前输入的 symbol。
- `ruff check sigma2 examples`、`ruff format --check sigma2 examples` 和 `git diff --check` 通过。
- 按用户要求，未编写或运行测试，也未运行示例；改动未提交。
