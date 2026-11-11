# PLAN-055：实施结果

- 完成时间：2026-11-12 01:27 CST
- 计划：`docs/dev/PLAN-055-input-schema.md`
- 设计：`docs/design/core-input-schema-20261112-overview.md`、`docs/design/bundle-20261111-overview.md`

## 结果与审阅

- 新增独立输入描述模块和 `rOperator.input_schema()`；读取实际签名，验证无环显式声明，返回结构副本并保留默认对象身份。普通类属性继承，查询不创建实例或校验行情。
- 为单 K 线、K 线截面、排名、盘口、成交和通用 Bundle 声明结构；市值加权补充 `market_cap` 说明。README 说明结构查询、实例需求和批量调用的边界。
- 用户确认恢复测试，并要求只做有意义的测试。新增针对性验收覆盖签名及声明错误、基础类迁移、数值与成交窗口 Bundle、空截面、排名历史和极小权重。
- `PYTHONPATH=.:pyta2 pytest -q tests/test_input_schema_current.py tests/test_bundle_current.py`：6 项通过；Ruff 检查与格式检查通过。
- 历史全套基线在本阶段完成前为 22 项失败、5 项通过、13 个收集错误，主要因仍引用已移除的旧输入对象、批量入口和生命周期；未为了本设计全面重写历史测试。
