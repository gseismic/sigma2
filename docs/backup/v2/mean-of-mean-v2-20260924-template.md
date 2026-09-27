# 基于 pyta2 MA 的两级均值 Signal V2

创建时间：2026-09-24 16:30 CST
修订时间：2026-09-26 16:02 CST

状态：原始方案已按[直接调用设计](direct-pyta2-20260926-overview.md)于 2026-09-26 调整。下文保留当时的接口与实现记录；当前代码直接使用两个 pyta2 MA，不再创建 `Pyta2Component` 或调用 `apply_component()`。

## 目标

保留 `rKlineMeanOfMean` / `KlineMeanOfMean` V1 原样，新建 V2 以 pyta2 已有的 MA 算法实现内外两级均值。V2 仍是 sigma2 的 K 线 Signal，自己定义输入字段、输出身份和生命周期；pyta2 只负责两级 MA 的计算与各自状态。

## 接口方案比较

| 方案 | 优点 | 问题 | 结论 |
| --- | --- | --- | --- |
| 改造 V1 增加 `ma_type` | 对外名称最少 | 破坏纯自算模板及已有训练列身份 | 不采用 |
| 组合两个 `rKlineMA` 子 Signal | 已有 sigma2 API 可复用 | 第二层要伪造一根 OHLCV K 线，字段语义错误 | 不采用 |
| V2 持有两个 pyta2 MA 指标 | 保留 V1；子指标只处理数值，K 线语义留在 sigma2 | 需要管理中间值和两个子指标修订 | 采用 |

公开类为 `rKlineMeanOfMeanV2(inner_n=3, outer_n=3, *, ma_type="SMA", field="close", ma_kwargs=None, **signal_kwargs)`，批量函数为同文件 `KlineMeanOfMeanV2(data, ...)`。`ma_type` 同时作用于内层和外层，支持 pyta2 `get_ma_class()` 当前的 SMA、EMA、WMA、HMA、DEMA、TEMA、KAMA、ZLEMA。`ma_kwargs` 同时传给两个组件，用于 KAMA 等高级参数；不得覆盖窗口或生命周期参数。需要两层不同 MA 类型时应另行设计明确的接口。

V2 的输出 schema key 仍为 `mean_of_mean`，训练列名与 V1 区分，例如 `mean_of_mean_v2(EMA(3),EMA(2))[close]`。每个组件的 full name 包含类型和窗口；KAMA 非默认 stride 需补入因子身份。`rKlineMeanOfMeanV2` 和 `KlineMeanOfMeanV2` 从 `sigma2.kline.trend`、`sigma2.kline` 导出，V1 导出保持不变。

## 内部状态与预热

V2 继承 `rKlineWindowSignal`，原始 K 线窗口长度为 `inner.required_window + outer.required_window - 1`。构造时用 `Pyta2Component` 分别适配两个 MA。每根调用通用的 `apply_component(inner_adapter, selected_field_array)`；内层达到自身所需观测数后，才把输出加入长度为 `outer.required_window` 的中间 deque 并调用 `apply_component(outer_adapter, middle_array)`。未到最终窗口前输出 `NaN`。内层已达到窗口却因输入缺失返回 `NaN` 时，仍把该值传给外层，交给 pyta2 MA 处理缺失值。

中间 deque 是 Signal 自有状态，列入公开的 `checkpoint_fields`；两个 pyta2 子指标由适配层调用各自的 `update_last()` 恢复，不列入父 Signal 检查点。`reset_window_extras()` 清空中间队列并重置两个组件。batch 只调用 `forward_signal_apply()` replay V2，不复制公式。公开扩展接口的取舍和错误语义见 `docs/design/pyta2-composition-api-20260924-overview.md`。

两级 MA 的其它内部调用写法、优缺点及未来取舍见 [组合写法对比](ma-of-ma-20260924-composition-options.md)。该文档是设计备忘，不改变本设计采用的适配对象方案。

## 三轮审阅

1. **公开用法**：V1 与 V2 各有独立名称和训练列；常见用法只加 `ma_type`，参数顺序与现有 `rKlineMA` 一致。
2. **正确性**：不能把 `inner_n + outer_n - 1` 当作所有 MA 的预热长度。HMA、DEMA、TEMA、KAMA、ZLEMA 的组件窗口可能更长；必须从组件的 `required_window` 推导。修订最后一根时，内外组件均通过 core 生命周期分派，父信号的中间队列恢复到观测前。
3. **边界**：高级参数只作用于 pyta2 MA，不得覆盖 `n`、buffer 或 return 生命周期参数。V2 使用公开的 `apply_component()`、`Pyta2Component` 和 `checkpoint_fields`；不能将子指标放入父 Signal 检查点。
