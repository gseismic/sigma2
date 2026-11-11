# 移除算子类中冗余配置只读属性：结果

- 创建时间：2026-11-12 02:59 CST
- 执行模型：Codex，环境标示基于 GPT-6；未提供可核实的完整模型 ID。
- 更新时间：2026-11-12 03:01 CST，更新模型同上；补充用户关于兼容性的明确决定。
- 更新时间：2026-11-12 03:05 CST，更新模型同上；提交前补正当前使用说明中的属性描述。
- 更新时间：2026-11-12 03:06 CST，更新模型同上；补充仓库锁定的 pyta2 版本验证。
- 实现范围：`WORKTREE`，基准提交 `b6b73b76e727de7e54d025f103057330c41e9c1a`。相关未提交内容包括 `sigma2/`、`examples/`、`tests/`、`docs/plans/` 和 `docs/HANDOFF.md`；工作区还保留了本任务前的其他未提交及未跟踪内容，结果尚未固定为提交。
- 计划：`docs/plans/PLAN-20261112-002-model-unknown-remove-redundant-properties.md`。

## 完成情况

- 移除计划清单中 18 个类的 43 个配置只读属性，覆盖 K 线指标、Outcome、pyta2 适配器和多标的算子；明确的属性清单见计划的“范围”。
- 内部计算和 `full_name` 改为直接使用原有私有配置或底层指标；适配器的 `history_window` 仅作为初始化局部变量。构造参数、核心状态和输出接口保留。
- 调整 `examples/006_kline_pyta2.py`、`examples/008_kline_missing.py`，新增 `tests/test_config_properties_current.py` 覆盖移除后的接口及非默认配置行为。提交前移除 `README.md` 和 `skills/sigma2-usage/` 中对已删除 `weights` 属性及实例配置属性的过时描述。

## 计划复核与偏差

原计划缺少明确的执行期行为测试，已在实施前补充。`rPyta2Signal` 的窗口长度只需要用于构造 deque，因此未保留重复的 `_history_window` 实例字段。未改变计划的公开接口删除范围。

## 验证

- 修改前及修改后对比 19 个配置场景，覆盖全部 18 个受影响类，包括非默认参数、缺失成交量和整根缺失 K 线，以及截面缺失：名称、输出字段、窗口信息和每一步结果一致。
- 当前契约及新增回归测试：44 项通过。命令：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=pyta2 /Users/mac/miniconda3/envs/py311/bin/python3.11 -m pytest -q tests/test_core_output_current.py tests/test_input_schema_current.py tests/test_bundle_current.py tests/test_config_properties_current.py`。
- 15 个独立示例运行通过；本次修改的 19 个 Python 文件 Ruff 检查和格式检查通过；`git diff --check` 通过。
- 提交前使用仓库 `pyproject.toml` 锁定的 pyta2 完整提交 `65071a84099c30a4d9476c327232da7c057b2caa`，重新运行上述 44 项当前测试及 15 个独立示例，均通过；与此前使用的本地 pyta2 提交分别验证。
- 全量 `pytest -q` 未能执行测试：13 个历史测试文件在收集阶段因引用已移除的接口而报错，例如 `KlineBar`、`sigma2.batch` 和 `sigma2.kline.pyta2`。该问题在修改前已存在，继续由 `TD-20261112-0209-001`（`docs/todos/TD-20261112-0209-001-current-test-suite.md`）跟踪；未将全量测试报告为通过。

## 遗留

用户已明确无需考虑兼容性，本次直接删除属性，不保留兼容层。历史测试的整体整理不在本次范围。记录时尚未提交或推送。
