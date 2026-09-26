# pyta2 子指标直接调用设计

创建时间：2026-09-26 15:43 CST

状态：已实施，见 [PLAN-025 实施结果](../dev/PLAN-025-direct-pyta2-calls-OUTCOME.md)。

## 背景与目标

`rKlineMeanOfMeanV2` 在 2026-09-24 的实现中，为调用两个 pyta2 MA 同时持有原指标和 `Pyta2Component`，再通过 `rSignal.apply_component()` 分派。用户希望直接使用 pyta2 类，不为方法名差异增加适配对象或 core 方法。本设计取代 [2026-09-24 的组件组合接口决策](pyta2-composition-api-20260924-overview.md)；旧文档保留为历史记录。

保留 `rSignal.step()/update_last()`、父 Signal 的末根检查点、`rKlineWindowSignal` 的 OHLCV 窗口和 `rPyta2Signal` 的 K 线字段绑定。`rPyta2Signal` 提供输入语义与 Signal 身份，不是待删除的纯方法适配对象。

## 方案比较

| 方案 | 优点 | 缺点 | 结论 |
| --- | --- | --- | --- |
| A. 保留 `Pyta2Component` + `apply_component()` | 分派集中，非 pyta2 子对象也可复用 | 一个 pyta2 指标要经过两个额外概念；调用路径长 | 淘汰 |
| B. 删除适配对象，让 `apply_component()` 自动识别 `rolling()` | 因子只持有原指标 | core 隐式识别 pyta2 风格，仍保留用户认为多余的方法 | 淘汰 |
| C. 因子直接选择子指标的 `rolling()` / `update_last()` | 调用与状态所有权可在本文件读懂；不增加概念 | 几个因子会重复很短的生命周期分支，并依赖现有内部 `_lifecycle_mode` | 采用 |
| D. 每个因子分别覆盖 `_step_forward()` / `_update_last_forward()` | 不读取 `_lifecycle_mode` | `rKlineWindowSignal` 的窗口追加与末根替换必须重复或重构，整体更复杂 | 淘汰 |

## 定稿规则

1. `rSignal` 继续在 `step()` 和 `update_last()` 进入计算前设置 `_lifecycle_mode`，异常时沿用现有 faulted 规则。该字段只作为仓库内部计算分支，不新增公开组件协议。
2. 使用 pyta2 指标的 Signal 直接持有原指标。在 `forward()` 中，`_lifecycle_mode == "update_last"` 时调用 `indicator.update_last(...)`，普通 `step` 时调用 `indicator.rolling(...)`；在 reset hook 中调用 `indicator.reset()`。
3. 单指标 K 线模板和 `rPyta2Signal` 历来允许测试直接调用 `forward()`，这种调用继续走 `rolling()`，但不会推进父 Signal 的索引或窗口。两级 MA V2 的 `forward()` 仅允许在父 Signal 的 `step()/update_last()` 期间调用，生命周期外先抛 `RuntimeError`，不得推进任一子指标。
4. 父 Signal 的自有中间值继续声明 `checkpoint_fields`，pyta2 子指标自行维护修订检查点，不进入父字段快照。外层只在内层达到 `required_window` 后收到观测；内层预热后的 `NaN` 仍送给外层。
5. 删除 `Pyta2Component` 类及导出、`rSignal.apply_component()`，不提供同义替代接口。它们是现行公开扩展入口，因此将包版本由 0.4.0 推进至 0.5.0；已有外部子类需改为直接调用所持子对象的新增/修订方法。
6. `rSignal` 对生命周期子对象的字段快照防护继续保留：子指标或子 Signal 必须自己修订，不能由父 Signal 深拷贝。非 pyta2 子对象也由其使用者直接调用 `step()/update_last()`。

## 代码形态

两级 MA 在 `forward()` 中只选择一次两个原指标的方法，预热与中间队列逻辑保持不变：

```python
mode = self._lifecycle_mode
if mode not in ("step", "update_last"):
    raise RuntimeError("forward() requires step() or update_last()")

inner_call = self._inner.update_last if mode == "update_last" else self._inner.rolling
outer_call = self._outer.update_last if mode == "update_last" else self._outer.rolling
inner_value = inner_call(values)
# 内层预热后，恢复过的中间队列加入当前结果，再调用 outer_call(middle)。
```

单指标桥接只需一个分支，并保留历史的直接 `forward()` 路径：

```python
if self._lifecycle_mode == "update_last":
    return self._indicator.update_last(*values)
return self._indicator.rolling(*values)
```

这些代码片段展示分派位置，不替代构造校验、预热处理或输出规范化。

## 三轮查漏补缺

1. **接口与命名**：`Pyta2Component` 和 `apply_component()` 都删除；不在 core 新增 `apply_pyta2()`、`apply_component_calls()` 或 `rolling()` 自动识别。`rPyta2Signal` 因为提供 K 线输入绑定而保留。
2. **状态与失败**：父队列在修订前恢复，子指标调用自己的 `update_last()`；连续修订、修订后续写和 warmup 阶段都应与完整重放相同。计算失败后不尝试局部修补子指标，统一由父 Signal 的 faulted 状态要求 reset/replay。
3. **兼容与验证**：移除两个公开入口并升级次版本；删除只验证旧接口存在的测试，保留数值、预热、批量、末根修订、异常与非 pyta2 子对象的行为验证。README、扩展指南和当前设计入口改为直接调用说明；历史 PLAN/OUTCOME 不改写。
