# 两级 MA 组合的子指标调用方式对比

创建时间：2026-09-24 21:25 CST
修订时间：2026-09-26 16:02 CST

状态：历史方案比较。2026-09-24 的实现采用方案 A；2026-09-26 按用户要求改为方案 C，并同时删除 `rSignal.apply_component()`，详见[直接调用设计](direct-pyta2-20260926-overview.md)。这里比较的是内部调用方式，不改变 `rKlineMeanOfMeanV2` / `KlineMeanOfMeanV2` 的用户接口或计算定义。

相关实现：`sigma2/kline/trend/mean_of_mean_v2.py`。当时接口依据见 [两级均值 V2 设计](mean-of-mean-v2-20260924-template.md)和 [组件组合接口设计](pyta2-composition-api-20260924-overview.md)；现行依据见[直接调用设计](direct-pyta2-20260926-overview.md)。

## 共同约束

- 父 Signal 的 `step()` 对内层调用 `rolling()`，并在内层预热完成后对外层调用 `rolling()`；父 Signal 的 `update_last()` 对已参与当前观测的子指标各自调用 `update_last()`。不能在父 Signal 修订时再次推进子指标。pyta2 对自身嵌套调用的自动修订，不会自动识别 sigma2 父 Signal 的生命周期。
- 内层达到 `required_window` 后才向外层送入一个观测。内层已预热但结果为 `NaN` 时仍送入外层，由 pyta2 处理缺失值。内外层的 `g_index` 可能不同，不能用子指标索引推断父 Signal 当前是新增还是修订。
- `_inner_values` 是父 Signal 自有的中间 deque，必须由 `checkpoint_fields` 在末根修订前恢复。两个 pyta2 指标各自维护检查点，不应进入父 Signal 的字段快照；重置时必须同时重置它们和中间 deque。
- 真实预热长度来自两个子指标的 `required_window`，即二者之和减一。SMA 以外的 MA 不能直接按 `inner_n + outer_n - 1` 计算。batch 继续重放同一个 Signal。
- 以下片段只展示生命周期分派。字段校验、MA 构造、输出身份、元信息与批量入口在各方案中相同。若保留当前 `forward()` 只能在父 Signal 生命周期内调用的契约，直接调用方案也必须检查调用时机。

## 方案 A：通用组件接口与 pyta2 适配对象（2026-09-24 实现）

```python
self._inner = ma_cls(self.inner_n, buffer_size=0, return_dict=False, **component_kwargs)
self._outer = ma_cls(self.outer_n, buffer_size=0, return_dict=False, **component_kwargs)
self._inner_component = Pyta2Component(self._inner)
self._outer_component = Pyta2Component(self._outer)

inner_value = self.apply_component(self._inner_component, values)
# 内层预热判断与中间 deque 更新
outer_value = self.apply_component(self._outer_component, middle)
```

`apply_component()` 根据父 Signal 的生命周期调用组件的 `step()` 或 `update_last()`；`Pyta2Component.step()` 再转发到 pyta2 的 `rolling()`。重置时调用两个适配对象的 `reset()`。

优点：生命周期分派在 core 中只实现一次；core 只依赖 `step/update_last` 协议，pyta2 的方法名留在适配层；同一个接口也能组合非 pyta2 子组件。父类负责拒绝生命周期外调用和无效组件。

缺点：这个因子同时保存两个原指标和两个适配对象；读代码时要跨越 `forward()`、`apply_component()` 和适配对象才能看到实际调用。适配对象不持有额外计算状态，主要提供方法名转换。

## 方案 B：在因子内定义 `_run_ma()`

```python
def _run_ma(self, indicator: rIndicator, values: np.ndarray) -> float:
    if self._lifecycle_mode == "step":
        return float(indicator.rolling(values))
    if self._lifecycle_mode == "update_last":
        return float(indicator.update_last(values))
    raise RuntimeError("MA 只能在 step() 或 update_last() 中调用")

inner_value = self._run_ma(self._inner, values)
# 内层预热判断与中间 deque 更新
outer_value = self._run_ma(self._outer, middle)
```

重置时直接调用 `_inner.reset()` 和 `_outer.reset()`。不再创建 `Pyta2Component`。

优点：因子只保存两个原指标；MA 的新增与修订调用可以在一个文件里读完；重复调用位置只写一次分派规则。

缺点：本质是把适配逻辑搬进因子，增加一个本地抽象；其它组合因子使用时还要复制它。因子直接依赖 `rSignal._lifecycle_mode` 的内部值，父类改变该实现细节时必须同步修改。与方案 A 相比，整体概念数量未明显减少。

## 方案 C：在 `forward()` 中直接选择两个方法

```python
mode = self._lifecycle_mode
if mode not in ("step", "update_last"):
    raise RuntimeError("forward() 只能在 step() 或 update_last() 中调用")

inner_call = self._inner.update_last if mode == "update_last" else self._inner.rolling
outer_call = self._outer.update_last if mode == "update_last" else self._outer.rolling

inner_value = inner_call(values)
# 内层预热判断与中间 deque 更新
outer_value = outer_call(middle)
```

重置方式同方案 B。这里先选好两个绑定方法，再按原逻辑完成预热和外层计算；外层尚未收到观测时不调用 `outer_call`。

优点：单个因子中的代码路径最短；没有适配对象或本地分派方法；新增与修订的实际调用一眼可见。

缺点：仍直接依赖 `_lifecycle_mode`。每个采用此写法的因子都要保留合法生命周期检查、方法选择和重置约定，容易在新增组合时漏掉一项。它缩短了局部代码，却不能自动降低整个库的维护成本。

## 方案 D：通用接口接收两种调用函数（未来可评估）

```python
inner_value = self.apply_component_calls(
    self._inner.rolling, self._inner.update_last, values
)
# 内层预热判断与中间 deque 更新
outer_value = self.apply_component_calls(
    self._outer.rolling, self._outer.update_last, middle
)
```

设想由 core 的 `apply_component_calls(on_step, on_update_last, *args, **kwargs)` 负责合法生命周期检查和调用分派，因子负责持有与重置原指标。它是候选接口，目前仓库中不存在。

优点：不需要适配对象，也不让因子读取 `_lifecycle_mode`；组件分派接口无需识别 pyta2，任意一对可调用方法均能接入。

缺点：每次调用都要传两种操作，公式更长；core 增加一种与现有 `apply_component()` 重叠的公开接口。若替换现有接口，还需迁移已有调用方并评估兼容性。方法对不提供重置入口，因子仍需显式重置原指标。

## 比较与取舍

| 维度 | A：适配对象 | B：本地方法 | C：直接选择 | D：函数对接口 |
| --- | --- | --- | --- | --- |
| 单个因子的可见代码 | 较多 | 中等 | 最少 | 调用处较长 |
| 生命周期规则的位置 | core + pyta2 适配层 | 每个因子的方法 | 每个因子的 `forward()` | core |
| 因子依赖父类内部模式 | 否 | 是 | 是 | 否 |
| 多种子组件复用 | 已支持 | 需复制或另写分派 | 需复制 | 可支持，需新增接口 |
| 对现有公共接口的影响 | 无 | 无 | 无 | 新增或迁移接口 |

2026-09-24 的判断：当时单指标桥接、K 线指标模板和非 pyta2 组件已使用 `apply_component()`，因此建议维持方案 A。若只看一个独立因子的代码量，方案 C 最短；方案 B 不推荐作为新的通用模板，因为它重复了适配层职责。方案 D 需要另行设计接口兼容路径。

2026-09-26 的定稿：用户明确要求不引入 `Pyta2Component` 与 `apply_component()` 两层概念，因此采用方案 C；相关调用方均直接使用原始子指标。上述比较继续保留，供以后评估局部代码量与全库抽象成本时参考。

## 三次核对

1. **接口边界**：方案 A 与 D 的组件分派均不依赖 pyta2 的类型或方法名；方案 B 与 C 虽不修改 core，却让因子依赖父类内部生命周期字段。core 的 schema 与缓存目前仍使用 pyta2 工具，不能据此声称整个 core 已与 pyta2 解耦。方案 D 是待讨论的新接口，不应误写成已实现能力。
2. **修订正确性**：四种方案都必须在父 Signal 修订时调用两个已参与当前观测的子指标的 `update_last()`，先恢复父队列，再重算当前内层输出。外层在内层预热之前从未推进，因此不会在那时收到修订调用。
3. **状态与成本**：四种方案都保留两个 pyta2 指标和中间 deque；只有 A 额外持有轻量适配对象。递推 MA 不能靠每次只对有限窗口重算来省掉子指标状态。没有性能测量时，不把适配层的常数开销当作取舍依据。
