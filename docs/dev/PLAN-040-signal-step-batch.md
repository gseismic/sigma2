# PLAN-040：恢复 MA、MACD 的批量入口

- 创建时间：2026-10-30 06:08 CST
- 设计：`docs/design/signal-step-batch-20261030-overview.md`
- 当前状态：已实施并静态审阅；按此前用户要求未编写或运行测试。实施时改动保留供审阅，用户于 2026-10-30 随后要求提交。

## 步骤

1. 借鉴 pyta2 `base/utils.py`，在 core 实现只依赖通用 Signal 的逐条重放，复用 `VectorTable` 和输出转换。
2. 补充 `KlineMA`、`KlineMACD` 并恢复相关导出，复用对应的逐条算子。
3. 将报错的 `01_kline_batch.py` 和 README 改为当前固定字段、schema 字段与元信息契约。
4. 静态审阅代码、记录结果和计划历史；不编写或运行测试，不自动提交。
