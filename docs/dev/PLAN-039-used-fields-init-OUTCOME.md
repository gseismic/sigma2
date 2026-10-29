# PLAN-039：实施结果

- 完成时间：2026-10-30 06:00 CST
- 计划：`docs/dev/PLAN-039-used-fields-init.md`
- 设计：`docs/design/kline-step-core-20261029-overview.md`

## 结果

- `rOperator.__init__` 接收可选的 `used_fields` 并保存在实例中，`rSignal`、`rOutcome` 将其转交给 core。
- MA、MACD、Boll 根据实例的 `field` 传入字段元信息；ATR 传入固定的 `high`、`low`、`close`。
- `None` 表示未声明，空元组可表示已声明不使用字段；两者不参与逐条输入校验。简单自定义信号仍可只实现 `forward`。
- 更新 README 和相关设计，保留已有 MACD 和波动指标改动。

## 审阅与检查

- 静态审阅了 core 构造参数转发、元信息读取和各指标字段来源；`used_fields` 不用于计算路径。
- `ruff check`、`ruff format --check` 和 `git diff --check` 通过。按用户此前要求未编写或运行测试；实施时未提交，用户随后要求提交。
