# PLAN-045：将 K 线截面价格排名改为收益率排名

- 创建时间：2026-10-30 15:00 CST
- 设计：`docs/design/kline-bundle-return-rank-20261030-overview.md`
- 状态：已实施并静态审阅；按用户要求未编写或运行测试，改动保留供审阅。

## 步骤

1. 以 `n` 表示回看截面数，实现 `close_t / close_(t-n) - 1` 的逐 symbol 排名和缺失语义，状态统一放在 `_state`。
2. 用 `rKlineBundleReturnRank` / `KlineBundleReturnRank` 替换旧价格排名出口；同步更新自包含示例和使用文档。
3. 静态审阅共同时间轴、窗口预热、动态 symbol、缺失、重置和批量重放；记录设计与结果。
