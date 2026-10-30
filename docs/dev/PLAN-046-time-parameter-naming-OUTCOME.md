# PLAN-046：实施结果

- 完成时间：2026-10-30 15:14 CST
- 计划：`docs/dev/PLAN-046-time-parameter-naming.md`
- 设计：`docs/design/time-parameter-naming-20261030-overview.md`

## 结果

- 在 README 中写入时间参数命名规范，区分 `n`、`lag`、`n_backward`、`n_forward`、`history_window` 和 `buffer_size`，说明窗口周期、端点距离及逻辑时间轴。
- 将 `rKlineReturn`、`KlineReturn`、`rKlineBundleReturnRank` 和 `KlineBundleReturnRank` 的收益率回看参数统一为 `lag`；实例属性、参数校验、状态窗口及 `n_backward` 同步更新，不保留旧 `n` 别名。
- 同步更新收益率排名设计、规范实施状态、使用指南和独立示例；指标周期 `n`、core 元信息及 Outcome 的 `n_forward` 继续使用原来的含义。
- 按设计稿，KDJ 的多个周期参数仍为 `n1`、`n2`、`n3`，具体名称另行确定，并已在 README 标明。

## 审阅与检查

- 静态审阅两个收益率算子的 `lag`、历史窗口与 `n_backward` 的对应关系，以及逐条和批量入口的参数一致性；只修改名称，不改变收益率公式、预热和状态推进。
- `ruff check sigma2 examples`、`ruff format --check sigma2 examples` 和 `git diff --check` 通过；现行代码、示例和使用说明中的收益率参数已使用 `lag`。
- 按用户要求，未编写或运行测试，也未运行示例。改动未提交，与此前工作区中的修改一起保留供审阅。
