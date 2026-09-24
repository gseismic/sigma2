# PLAN-024 实施结果：pyta2 MA 两级均值 V2 与通用组件接口

完成时间：2026-09-24 16:56 CST

对应计划：`docs/dev/PLAN-024-mean-of-mean-v2.md`。对应设计：`docs/design/mean-of-mean-v2-20260924-template.md`、`docs/design/pyta2-composition-api-20260924-overview.md`。

## 实施摘要

- 保留原 `rKlineMeanOfMean` / `KlineMeanOfMean` V1 实现与文件，新增 `rKlineMeanOfMeanV2` / `KlineMeanOfMeanV2`。V2 用两个 pyta2 MA 组件实现两级均值，`ma_type` 支持 SMA、EMA、WMA、HMA、DEMA、TEMA、KAMA、ZLEMA；`ma_kwargs` 共同传给内外两层，KAMA 的 stride 进入训练列身份。
- V2 从两个组件的真实 `required_window` 推导预热，使用一个有界中间 deque，并通过公开的 `checkpoint_fields` 在末根修订前恢复该队列。在线与 batch 共用同一 `step()` replay 实现，新增 `examples/08_mean_of_mean_v2.py`、family 导出、README 和使用指南。
- `rSignal` 删除 pyta2 专属的 `_apply_pyta2()` / `apply_pyta2()`，增加通用的 `apply_component()`，按父 Signal 的 `step/update_last` 生命周期调用组件对应方法。`Pyta2Component` 位于 `sigma2.utils.pyta2` 并从包顶层导出，只在适配层映射 pyta2 的 `rolling/update_last/reset`。已有单指标桥接、内置 K 线因子和组合测试均迁移。
- 旧 `_update_state_fields` 继续兼容；新组合推荐公开的 `checkpoint_fields`。基类拒绝把具有独立修订生命周期的子对象深拷贝进父字段检查点。旧 `_apply_pyta2()` 是受保护入口，没有在基类保留别名；下游直接调用它的子类需迁移。

## 验证与审阅

- `pytest -q`：119 passed，1 skipped（可选依赖）。覆盖八种 MA 的独立 pyta2 结果对照、V1 SMA 一致性、KAMA 参数、预热期与连续末根修订、续写、batch、通用非 pyta2 子组件和接口错误。
- `ruff check sigma2 tests examples`、所改 Python 文件的 `ruff format --check`、`python -m compileall -q sigma2 tests examples`、`git diff --check` 均通过。
- `python -m examples.07_mean_of_mean` 和 `python -m examples.08_mean_of_mean_v2` 可运行；在线修订、续写与 batch replay 输出一致。
- 代码审阅后移除内置 K 线因子的重复 pyta2 类型检查，并补充 `Pyta2Component` 包顶层公开导入与拒绝错误对象的验证。

## 边界

此次解开的是 **组件生命周期接口** 的 pyta2 专属耦合。core 的 schema 与短输出缓存仍复用 pyta2 工具，安装依赖未变化。`forward()` 是计算钩子；V2 组合应通过父 Signal 的 `step/update_last` 调用，不直接作为可推进的公共入口。
