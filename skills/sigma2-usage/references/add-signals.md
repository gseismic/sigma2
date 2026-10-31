# 扩展 sigma2 算子

先看仓库 `AGENTS.md`、目标数据类型和 `sigma2/__init__.py`。公开接口需要新的设计取舍时先设计。单 K 线实现可参考 [`rKlineMA`](../../../sigma2/kline/trend/ma.py)、[`rKlineMACD`](../../../sigma2/kline/trend/macd.py)和 [`rKlineFutureReturn`](../../../sigma2/kline/outcome/future_return.py)；成交自定义实现参考 [示例](../../../examples/202_trade_custom_signal.py)。

## 选择基类

| 输入和时间语义 | 基类 |
| --- | --- |
| 当前单 K 线结果 | `rKlineSignal` |
| 当前 K 线截面结果 | `rKlineBundleSignal` |
| 等待后续 K 线的结果 | `rKlineOutcome` |
| 盘口快照 | `rOrderBookSignal` |
| 逐笔成交 | `rTradeSignal` |

Signal 只能使用当前及以前的数据。Outcome 的 `n_forward` 是固定后续观测数，`result_index` 是结果所属锚点；回填到锚点不代表当时可用。当前 Bundle 提供 Signal 基类、收益率排名和加权价格指数。

## 实现约定

- 数据类型基类定义固定的 `step` 输入并调用 `super().step()`。简单自定义类只需要实现相同字段的 `forward`，返回字典；不要在子类复制生命周期逻辑。
- 可在构造函数通过 `super().__init__` 指定 `schema`、`n_backward`、`buffer_size` 和 `used_fields`；Outcome 还需提供 `n_forward`。`used_fields` 根据构造参数声明，只用于元信息。
- 子指标、输入窗口和递推数值使用普通实例属性。历史修订或计算失败时新建实例并重放；不要求对象支持深复制。
- `schema` 可使用 pyta2 `Space`；省略时按首个结果固定字段，缓存为 object 类型。输出必须是字典，键与 schema 一致。
- K 线缺失由 `is_missing=True` 表示；算法使用可选 volume 时应处理 `None`。上游负责输入格式，不能添加逐字段必需检查。
- `n_backward` 不含结果位置，`min_periods = n_backward + 1 + n_forward`。只保留算法实际需要的输入窗口；pyta2 的缺失处理交由 pyta2 自身负责。
- 单周期技术指标使用 `n`；过去端点与当前观测相隔的步数使用 `lag`，调用参数和实例属性统一命名。多个指标周期按含义区分；时间参数说明见仓库 README。
- 对外批量函数创建 `buffer_size=0` 的实例后调用 `forward_step_apply`，不要维护第二套公式；Outcome 的批量结果按锚点对齐。
- 更新相关导出和独立示例；检查数据时点、缺失、失败处理和结果对齐。验证方式以用户要求和仓库指令为准。
