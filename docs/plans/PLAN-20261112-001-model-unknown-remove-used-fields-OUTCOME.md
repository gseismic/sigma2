# 移除 used_fields：实施结果

- 创建时间：2026-11-12 02:10 CST
- 执行模型：Codex，环境标示基于 GPT-6；未提供可核实的完整模型 ID。
- 分析与结果范围：`WORKTREE`，基准提交 `b6b73b76e727de7e54d025f103057330c41e9c1a`。本次改动涉及 `sigma2/core/`、各具体算子、`examples/`、`tests/test_core_output_current.py`、`README.md`、`skills/sigma2-usage/`、本计划及结果，并新增 `docs/TODOS.md` 和相关详情。任务前已有的 `AGENTS.md`、`pyproject.toml` 改动及未跟踪的 `GOAL.md`、`fintools`、`minbt`、`pyta2` 软链接未纳入本次修改；工作区尚未固定为提交。
- 关联计划：`docs/plans/PLAN-20261112-001-model-unknown-remove-used-fields.md`。

## 完成情况

- 从 `rOperator`、`rSignal`、`rOutcome` 删除字段清单的构造参数、存储、属性和元信息；具体算子不再声明该清单。
- 保留实际参与计算的 `field`、`fields` 和 `reference_field`；更新当前示例、README、仓库使用 skill 及相关测试。历史设计保留原状，README 标明以当前说明和源码为准。
- 用户明确不要求兼容旧接口，未添加迁移层或替代的通用字段清单。

## 验证结果

- Python 3.11 环境使用任务前的 `pyproject.toml` 和本地 `pyta2` 软链接；`pyta2` 实际提交为 `20e22e6565766c979fee1facd23eba36dbf518f5`，其工作区无未提交改动。
- 当前契约测试：`tests/test_core_output_current.py`、`tests/test_input_schema_current.py`、`tests/test_bundle_current.py`，共 17 项通过；包含 Signal 和 Outcome 的接口及批量元信息检查。
- `examples/` 下 15 个独立示例全部运行通过，覆盖 K 线、Bundle、盘口、成交、Outcome 和 pyta2 桥接。另验证成交量均线、按成交量计算未来变化及按开盘价计算未来高低价变化的结果。
- 本次修改的 Python 文件通过 Ruff 检查；仓库使用 skill 通过 `quick_validate.py`；`git diff --check` 通过。当前源码、示例、README 和使用 skill 中没有 `used_fields` 残留。
- 全量 `pytest -q` 在修改前后均于收集阶段出现相同的 13 个历史测试文件导入错误，涉及 `KlineBar`、`sigma2.batch` 等已移除接口；全套测试因此没有执行，不能声称通过。

## 计划偏差与遗留事项

- 未改变实施范围。因历史测试妨碍全量验证，按项目规范登记待评估事项 `TD-20261112-0209-001`，见 `docs/todos/TD-20261112-0209-001-current-test-suite.md`；本次未迁移历史测试。
- 本次未提交或推送。
