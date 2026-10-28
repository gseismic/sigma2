# PLAN-029：README 与使用 skill 更新结果

完成时间：2026-10-28 15:24 CST
计划：[PLAN-029-readme-skill-warmup.md](PLAN-029-readme-skill-warmup.md)

## 实施结果

- README 和 `skills/sigma2-usage` 说明 `n_backward`、`n_forward` 与 `min_periods`，以 SMA(20) 解释前置 19 根加当前 1 根；补充行情缺口和递推状态对预热的影响。
- 根据用户后续确认的字典协议，同步单 K 线、Bundle、字段映射、可选元信息和未来结果对齐的示例与扩展说明；标准 OHLC 使用 `open/high/low/close`。
- 新增 `examples/10_mapping_inputs.py`，展示 `date` 到输入 `open_time` 的映射、成交量字段映射和截面排名。算子接口实施详见 [PLAN-030 结果](PLAN-030-kline-mapping-OUTCOME.md)。

## 审查与验证

- README 的 4 个 Python 代码块分别执行成功。
- 10 个编号示例均从 `examples` 目录直接运行成功。
- 与 PLAN-030 一起完成完整回归：`python3 -m pytest -q` 为 213 项通过；`ruff check sigma2 tests examples` 和 `git diff --check` 通过。

提交与推送状态以 git 记录为准。
