# sigma2 交接文档

> 2026-11-12 02:59 CST 进展：本交接的 MA 属性及其他类的类似配置只读属性已移除；下文“尚未修改”描述的是交接时状态。执行结果、兼容性影响及验证见 `docs/plans/PLAN-20261112-002-model-unknown-remove-redundant-properties-OUTCOME.md`。

- 更新时间：2026-11-12 02:23 CST
- 更新模型：Codex，环境标示基于 GPT-6；未提供可核实的完整模型 ID。
- 范围：`WORKTREE`，基准提交 `b6b73b76e727de7e54d025f103057330c41e9c1a`。工作区包含本会话未提交的代码、示例和文档，以及任务前已有的改动和未跟踪文件；详见下文。当前状态尚未固定为提交。

## 项目背景和用户偏好

- `GOAL.md` 定义项目目标：按数据类型组织量化交易信号库，`sigma2/core` 为核心，K 线、成交、盘口和多 symbol K 线分别组织输入接口。只有用户明确要求时才能修改 `GOAL.md`。
- 用户的代码哲学是极简：接口应从实际使用场景判断必要性，避免为了可能的未来需求保留概念。
- 继续工作前应读取根目录 `GOAL.md`、`AGENTS.md`，检查 `git status`，结合当前代码核实历史文档。之前的交接内容保存于基准提交的 `docs/HANDOFF.md`，其中 `update_last()` 等描述已过时，不应作为当前契约。

## 当前交接点：MA 的三个属性

用户询问 `sigma2/kline/trend/ma.py` 中 `rKlineMA.field`、`n`、`ma_type` 三个只读属性是否有必要，并要求写交接文档，让别人继续处理。前一轮仅做分析，**尚未修改或移除这三个属性**；用户也尚未明确指定要删除它们，接手时按用户后续的具体指令确定操作范围。

已确认的事实：

- `field` 返回 `self._field`，当前 `forward()` 用 `self.field` 选择输入字段，`full_name` 也使用它。若决定移除该属性，需要同步处理这两处读取，保留字段选择功能。见 `sigma2/kline/trend/ma.py:38`、`sigma2/kline/trend/ma.py:66` 和 `sigma2/kline/trend/ma.py:84`。
- `n` 返回内部指标的周期，`ma_type` 返回内部指标的名称；具体均线类型和周期在构造内部指标时已确定，计算由内部指标执行。见 `sigma2/kline/trend/ma.py:30`、`sigma2/kline/trend/ma.py:38` 和 `sigma2/kline/trend/ma.py:76`。
- 搜索当前仓库时，外部示例只有 `examples/008_kline_missing.py:26` 打印 `ma.field`；该行是在本会话同步示例时加入的。未发现直接读取 `rKlineMA.n` 或 `rKlineMA.ma_type` 的仓库内调用，仓库外使用情况未知。
- `full_name` 可用于展示配置，例如 `EMA(5)[volume]`，但它是字符串，不能替代结构化属性查询。`n_backward` 和 `min_periods` 描述时序，不能普遍当作 `n` 的替代；见 `README.md` 的时间参数说明。
- 当前三个属性对外只读。如果决定精简，应保留计算真正依赖的内部字段及指标，不要仅把它们改为可随意赋值的公开状态；运行中变更字段可能混入历史窗口，改变一个独立的公开周期值也不等于改变内部指标。

前一轮的**建议**是：若没有程序从既有实例反查字段、周期和均线类型的需求，可以移除三个公开属性。它们的实际价值是支持这样的结构化反查；该建议不等同于用户已经决定删除，也不自动扩展到其他算子。

## 本会话已完成：移除 used_fields

用户已明确要求移除 `used_fields`，并就该次移除说明不考虑兼容性。该授权针对 `used_fields`，不应自动解释为对其他接口变化的决定。

- 已从 `rOperator`、`rSignal`、`rOutcome` 删除构造参数、存储、属性及 `meta_info` 字段；各内置算子不再向基类声明它。
- 已同步当前 `README.md`、`examples/`、`skills/sigma2-usage/` 和 `tests/test_core_output_current.py`。具体算子用于计算的 `field`、`fields`、`reference_field` 等配置保留。
- 计划与结果分别为 `docs/plans/PLAN-20261112-001-model-unknown-remove-used-fields.md` 和 `docs/plans/PLAN-20261112-001-model-unknown-remove-used-fields-OUTCOME.md`，索引为 `docs/plans/INDEX.md`。以上变更尚未提交或推送。

## 验证与待评估事项

本会话上一项代码修改后验证过：

- 当前契约测试 17 项通过；15 个独立示例运行通过；本次修改的 Python 文件 Ruff 检查通过，仓库使用 skill 的格式验证通过。
- 额外验证了成交量均线、按成交量计算未来变化和按开盘价计算未来高低价变化。
- 全量 `pytest -q` 在修改前后均因 13 个历史测试文件引用已移除接口而在收集阶段失败；全套测试没有执行。相关整理建议登记为待评估的 `TD-20261112-0209-001`，见 `docs/TODOS.md` 和 `docs/todos/TD-20261112-0209-001-current-test-suite.md`，并非本次移除 MA 属性的授权。
- 上述运行使用 Python 3.11 和本地 `pyta2` 软链接；验证时 `pyta2` 的提交为 `20e22e6565766c979fee1facd23eba36dbf518f5`。工作区的 `pyproject.toml` 是任务前已有改动。

可复现当前契约测试的命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=pyta2 /Users/mac/miniconda3/envs/py311/bin/python3.11 -m pytest -q tests/test_core_output_current.py tests/test_input_schema_current.py tests/test_bundle_current.py
```

## 工作区保护

- 任务开始前已修改的文件：`AGENTS.md`、`pyproject.toml`。
- 任务开始前已有未跟踪项：`GOAL.md` 和本地软链接 `fintools`、`minbt`、`pyta2`。不要清理、覆盖或无区别暂存它们。
- 本会话未提交改动涉及 `sigma2/`、`README.md`、`examples/`、`skills/sigma2-usage/`、`tests/test_core_output_current.py`，以及新增的 `docs/plans/`、`docs/TODOS.md`、`docs/todos/`；本交接还更新了 `docs/HANDOFF.md`。接手前请以 `git status --short --untracked-files=all` 和实际差异为准。
- 如后续修改或提交，应区分本会话成果和用户原有改动；不得擅自回滚、覆盖或混入无关文件。
