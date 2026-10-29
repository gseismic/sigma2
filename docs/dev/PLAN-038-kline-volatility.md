# PLAN-038：精简单 K 线波动指标并移除均值组合

- 创建时间：2026-10-30 05:52 CST
- 设计：`docs/design/kline-volatility-20261030-overview.md`
- 当前状态：已实施并静态审阅；按用户此前要求未编写或运行测试。实施时改动保留供审阅，用户于 2026-10-30 随后要求提交。

## 步骤

1. 删除 `mean_of_mean.py`、`mean_of_mean_v2.py` 和对应的公开导出，标记依赖这些类的旧示例与文档。
2. 将 ATR、Boll 改为直接继承 `rKlineSignal`，分别在 `_state` 中保存 pyta2 指标和所需字段窗口；使用 pyta2 字典输出与 schema。
3. 移除尚未迁移的 ATR、Boll 批量入口及直接导出，更新 README。
4. 静态审阅代码、更新计划结果和历史；不编写或运行测试，不覆盖已有 MACD 改动。
