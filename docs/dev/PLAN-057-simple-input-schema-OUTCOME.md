# PLAN-057：实施结果

- 完成时间：2026-11-12 01:53 CST
- 计划：`docs/dev/PLAN-057-simple-input-schema.md`
- 设计：`docs/design/input-schema-simple-20261112-overview.md`

## 结果与审阅

- 按用户确认的方案，将输入声明改为字典列表；嵌套值按需使用 `fields`、`values`、`items`，无须编写旧的递归节点格式。
- `sigma2/core/input_schema.py` 从 229 行缩减为 66 行。查询保留真实签名、必要的顶层声明检查、独立描述副本、普通继承和默认对象身份；不再递归校验类型词汇或嵌套内容，也不逐条验证行情。
- 迁移各数据类型及具体算子的声明，并更新 README 和设计入口。`input_schema()` 的外层 `parameters` 结构保留，旧字典式声明、嵌套 `fields` 字典及依赖 `nullable`/`enum` 的调用方需要迁移。
- 审阅确认单 K 线和截面计算路径未改动；K 线排名将 `close` 和 `is_missing` 描述为可省略，市值与价格要求保留为条件说明。

## 验证

- 按用户要求只运行必要的针对性测试：`PYTHONPATH=.:pyta2 pytest -q tests/test_input_schema_current.py tests/test_bundle_current.py`，7 项通过。覆盖签名、列表声明、多层嵌套、自由描述、继承与副本、顶层错误，以及 K 线和 Bundle 原有调用。
- `ruff check`、`ruff format --check`、`python -m compileall -q sigma2` 和 `git diff --check` 通过。
- 未重新运行已知使用旧接口的历史全量测试；其此前基线问题见 `docs/dev/PLAN-056-core-output-contract-OUTCOME.md`。原有 `pyproject.toml` 修改及未跟踪文件未纳入本次改动。
