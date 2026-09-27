# 无 pyta2 指标的 K 线组合 Signal 模板

创建时间：2026-09-24 16:19 CST

## 目标与边界

用两级简单移动均值验证 `rKlineSignal` 的自有状态、`step()`、`update_last()`、`reset()`、输出 schema 和 batch replay。因子源码不导入或调用 pyta2 指标。当前 sigma2 core 仍使用 pyta2 的 schema/缓存工具，包安装依赖也仍包含 pyta2；本次的“不依赖 pyta2”指因子计算和因子源码，不宣称整个包可在未安装 pyta2 时运行。

输入为一根 OHLCV K 线，`field` 可选标准字段。内层计算最近 `inner_n` 根所选值的简单均值；外层计算最近 `outer_n` 个**有效内层均值**的简单均值。所需原始 K 线数为 `inner_n + outer_n - 1`，此前输出 `NaN`。任何窗口中有 `NaN` 时对应输出为 `NaN`，异常值滑出后恢复正常。每个实例只处理一条流。

## 公开接口方案

| 方案 | 优点 | 代价 | 判断 |
| --- | --- | --- | --- |
| 复用两个 pyta2 `rSMA` | 代码短，算法复用 | 不符合本次无 pyta2 指标的验证目标，也绕不开子指标生命周期 | 不采用 |
| `rKlineWindowSignal` 每根重算完整历史 | 无额外递推状态，易审计 | 不能检验自有状态检查点；每根扫描全部原始窗口 | 不作为本次模板 |
| `rKlineSignal` 持有两个有界 deque | 明确展示组合状态及修订恢复；无指标依赖 | 每根对窗口求和，复杂度为 `O(inner_n + outer_n)` | 采用 |

公开类为 `rKlineMeanOfMean(inner_n=3, outer_n=3, *, field="close", **signal_kwargs)`；同文件批量函数为 `KlineMeanOfMean(data, inner_n=3, outer_n=3, *, field="close", return_type="dict", return_meta_info=False)`。输出 schema key 为 `mean_of_mean`，训练列名为 `mean_of_mean(3,3)[close]`；所有影响数值的参数进入 `full_name`。实现位于 `sigma2/kline/trend/mean_of_mean.py`，由 `sigma2.kline.trend` 和 `sigma2.kline` 导出。该示例暂不提升到包顶层。

## core 扩展点

目前 `rSignal(schema=...)` 要求 pyta2 `Space`，使纯计算的自定义 Signal 也必须引入 pyta2 类型。增加简写 `schema={"mean_of_mean": np.float64}`：core 将 dtype 规范化为带 `.dtype` 的输出字段，继续支持已有 pyta2 `Schema`/`Space` 输入，并保持 batch dtype 与输出缓存行为。简写只表示输出 dtype，不添加范围约束。因子作者仍需正确处理预热与缺失值。

## 三轮审阅

1. **语义和命名**：两级均值不是一次对原始价格求均值；外层只接收有效内层均值。`inner_n=1` 或 `outer_n=1` 仍按同一公式工作。`full_name` 包含两个窗口和字段，避免不同参数的训练列冲突。
2. **状态和修订**：两个 deque 都列入 `_update_state_fields`。core 在新观测前保存它们，在修订末根前恢复；`forward()` 只消费一根观测。连续修订和修订后继续 `step()` 必须与最终数据重新构造的实例一致。
3. **边界和兼容**：窗口参数必须是正整数且不能为 bool；`field` 只接受标准 OHLCV 名称。原有 pyta2 schema 路径保持原样，新 dtype 路径不改变 pyta2 适配器。文档明确运行时依赖仍存在，避免把源码独立误写成安装独立。
