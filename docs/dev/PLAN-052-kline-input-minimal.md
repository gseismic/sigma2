# PLAN-052：精简单 K 线输入处理

- 创建时间：2026-11-11 21:43 CST
- 设计：`docs/design/kline-missing-input-20261111-overview.md`
- 状态：已实施并静态审阅；按用户此前要求未编写或运行测试及示例。

## 步骤

1. 删除 `_KlineStep.step()` 对 `is_missing` 的类型检查及 OHLCV 自动替换，保留固定签名和 `super().step()` 原样转发。
2. 静态核对 `super()` 的方法解析顺序和 core 生命周期；核对 `sigma2.kline` 已导出 `rKlineSignal`、`rKlineOutcome`。
3. 更新 README、使用指南和缺失数据示例，明确上游使用 NaN 表示缺失字段，`is_missing` 不再自动改写字段。
4. 静态审阅改动，并遵照用户此前要求不编写或运行测试、不运行示例；使用 Ruff 和差异检查验证语法及格式。
5. 记录实施结果并追加历史索引，按仓库规范提交并立即推送，不纳入原有用户修改。
