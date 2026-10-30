# PLAN-045：实施结果

- 完成时间：2026-10-30 15:03 CST
- 计划：`docs/dev/PLAN-045-kline-bundle-return-rank.md`
- 设计：`docs/design/kline-bundle-return-rank-20261030-overview.md`

## 结果

- 将截面价格排名替换为 `rKlineBundleReturnRank`，用 `close_t / close_(t-n) - 1` 计算各 symbol 的 n 步收益率，再按指定方向排名；批量入口为 `KlineBundleReturnRank`。
- 使用最近 n 个截面的有效收盘价映射，在共同时间轴上回看，避免 symbol 缺席后误用更早价格；状态放在 `_state`，由 core 重置。
- 保留每个当前 symbol 的排名，首 n 个截面和端点缺失、参考价为零、收益率非有限的 symbol 返回 NaN；并列取平均名次。`None` 收盘价作为缺失处理，解决此前审查发现的排名算子故障问题。
- 更新公共导出、独立示例、README、使用指南及设计入口。此前已归档的旧 Bundle 代码没有改动。

## 审阅与检查

- 静态审阅 n 步回看、预热、动态 symbol、缺失截面、重置和批量缓存；`open_time` 不自动补齐时间轴，调用方需为每个逻辑时点提交截面。
- `ruff check sigma2 examples`、`ruff format --check sigma2 examples`、`git diff --check` 通过；源码和现行使用文档不再引用被替换的价格排名 API。
- 按用户要求，未编写或运行测试，也未运行示例。此前审查指出的加权指数极端权重下溢问题不在本次排名改造范围，仍待修复，已在文档标明。改动未提交。
