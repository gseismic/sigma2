# PLAN-023 执行结果：无 pyta2 指标的两级均值 Signal 模板

完成时间：2026-09-24 16:26 CST

对应计划：`docs/dev/PLAN-023-mean-of-mean-template.md`

设计文件：`docs/design/mean-of-mean-20260924-template.md`

## 结果

- 新增 `sigma2/kline/trend/mean_of_mean.py`：`rKlineMeanOfMean(inner_n, outer_n, field=...)` 自行维护两个有界 deque，`KlineMeanOfMean(...)` 逐行重放同一 Signal。输出预热长度为 `inner_n + outer_n - 1`，支持最近一根反复修订、重置、字段绑定与稳定训练列名。
- `rSignal` 新增 `schema={"value": np.float64}` dtype 简写；原有 pyta2 `Schema`/`Space` 输入仍按旧路径处理。因子源码无 pyta2 导入或指标调用。
- 新增 `examples/07_mean_of_mean.py`，更新 family 导出、README、使用 skill 和扩展指南。

## 审阅与验证

- 审阅了状态快照、两层均值预热、`NaN` 滑出后的恢复、连续 `update_last()`、修订后续写、batch 字段绑定与旧 schema 兼容路径。
- `python -m pytest -q`：93 passed。
- `python -m examples.07_mean_of_mean`：输出修订值 2.5、续写值 4.0，batch 与在线结果一致。
- `ruff check sigma2 tests examples`、本次改动的六个 Python 文件 `ruff format --check`、`python -m compileall -q sigma2 tests examples` 和 `git diff --check` 通过。
- 全仓库 `ruff format --check sigma2 tests examples` 仍报告 11 个本次未改动文件格式不符；未批量改写无关文件。

## core 结论与边界

现有 core 的状态检查点足以支持一个不调用 pyta2 指标的两级有状态计算；直接遇到的扩展缺口是输出 schema 原本只接受 pyta2 `Space`，本次已补充 dtype 简写。sigma2 core 仍导入 pyta2 `Schema`、`DequeTable` 和 `rIndicator`，包运行与安装仍依赖 pyta2。本次验证的是**因子计算和因子源码独立**，不是整个 core 的运行时脱钩。后者若需要，应单独设计和实施。
