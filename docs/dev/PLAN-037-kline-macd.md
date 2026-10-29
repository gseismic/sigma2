# PLAN-037：按 MA 方式精简单 K 线 MACD

- 创建时间：2026-10-30 05:44 CST
- 设计：`docs/design/kline-macd-20261030-overview.md`
- 当前状态：已实施并静态审阅；按用户此前要求未编写或运行测试。实施时改动保留供审阅，用户于 2026-10-30 随后要求提交。

## 步骤

1. `rKlineMACD` 直接继承 `rKlineSignal`，创建 pyta2 MACD 并让它直接返回字典；将指标和单字段窗口放入 `_state`。
2. 保持固定 K 线输入、实例参数与 `used_fields`，复用 pyta2 的 schema、预热、参数校验、公式名及缺失行为。
3. 移除依赖旧 batch 的 `KlineMACD` 入口及直接导出，更新 README 和设计说明。
4. 静态审阅和检查代码，记录结果并追加计划历史；不编写或运行测试。
