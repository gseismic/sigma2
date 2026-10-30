# PLAN-043：重建 K 线截面 Signal 与价格排名

- 创建时间：2026-10-30 06:43 CST
- 设计：`docs/design/kline-bundle-price-rank-20261030-overview.md`
- 状态：已实施并静态审阅；按用户要求未编写或运行测试，改动保留供审阅。

## 步骤

1. 实现只定义固定输入并调用 core 的 `rKlineBundleSignal`，支持自定义 Signal 仅重载 `forward`。
2. 实现 `rKlineBundleRank` 及批量入口，按输入 symbol 返回排名，明确缺失、并列和排序方向。
3. 更新包导出、README 和现有设计状态；增加按分级编号命名的独立示例。
4. 静态审阅 core 缓存和 pyta2 重放接口，按用户要求不编写或运行测试；记录实施结果和计划历史，改动保留供审阅。
