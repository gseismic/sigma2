# PLAN-025 实施结果：直接调用 pyta2 子指标

完成时间：2026-09-26 16:02 CST

对应计划：[PLAN-025-direct-pyta2-calls.md](PLAN-025-direct-pyta2-calls.md)。对应设计：[direct-pyta2-20260926-overview.md](../design/direct-pyta2-20260926-overview.md)。

## 实施摘要

- 删除 `Pyta2Component` 类、包导出及 `rSignal.apply_component()`，包版本从 0.4.0 升至 0.5.0。现行代码不提供同义替代接口；外部扩展若用过这些入口，需要直接调用所持子对象的新增、修订和重置方法。
- `rKlineMeanOfMeanV2` 直接持有内外两个 pyta2 MA，按父 Signal 当前生命周期选择各自的 `rolling()` / `update_last()`，重置时调用两个指标的 `reset()`。保留中间队列检查点、真实预热长度、输出身份和生命周期外 `forward()` 的防护。
- `rPyta2Signal` 与内部 K 线单指标模板直接调用原指标。两者保留历史上直接调用 `forward()` 时推进子指标、但不推进父 Signal 的行为；`rPyta2Signal` 在构造指标之前校验其类是否继承 pyta2 `rIndicator`。
- 盘口组合与非 pyta2 子对象测试改为显式调用各自的新增/修订方法。README、扩展指南与现行设计入口同步到直接调用规则；2026-09-24 的方案文档标记为历史资料，未改写旧 PLAN/OUTCOME。

## 验证与审阅

- `pytest -q`：118 passed。覆盖八种 MA 的 pyta2 数值对照、warmup 阶段与连续末根修订、修订后续写、batch replay、通用 pyta2 桥接、盘口组合和非 pyta2 子对象。
- `ruff check sigma2 tests examples`：通过。对本次改动的 11 个 Python 文件执行 `ruff format --check`：通过。`python -m compileall -q sigma2 tests examples` 与 `git diff --check`：通过。
- `python -m examples.05_pyta2_bridge` 与 `python -m examples.08_mean_of_mean_v2`：运行通过。修改过的 Markdown 相对链接检查通过。
- 全量测试初次发现非 pyta2 类在构造前抛出不明确的参数错误，现已把继承检查移至构造前并重新通过全量测试。审阅确认 V2 在生命周期外不会推进内外子指标，直接分派没有改动中间队列与子指标检查点的状态所有权。

## 边界

此次删除的是子指标方法适配层。子类为直接调用 pyta2 指标，需要读取父 Signal 的内部 `_lifecycle_mode`；`rSignal` 的 schema 和缓存仍使用 pyta2 工具，安装依赖不变。`rPyta2Signal` 仍作为有 K 线字段绑定和 Signal 身份的用户入口保留。
