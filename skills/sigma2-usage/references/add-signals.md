# 扩展 sigma2 算子

先看仓库 `AGENTS.md`、目标 family 和 `sigma2/__init__.py`。公开接口需要新的设计取舍时先设计。现有模板包括 [`rKlineMeanOfMean`](../../../sigma2/kline/trend/mean_of_mean.py)、[`rKlineMeanOfMeanV2`](../../../sigma2/kline/trend/mean_of_mean_v2.py)和[自定义成交信号](../../../examples/06_custom_signal.py)。

## 选择时间语义和输入

| 输入 | 当前结果 | 等待未来观测的结果 |
| --- | --- | --- |
| 单 symbol `KlineBar` | `rKlineSignal` / `rKlineWindowSignal` | `rKlineOutcome` / `rKlineWindowOutcome` |
| 同时点 `KlineBundle` | `rKlineBundleSignal` / `rKlineBundleWindowSignal` | `rKlineBundleOutcome` / `rKlineBundleWindowOutcome` |
| 盘口或成交事件 | 对应 `rOrderBookSignal` / `rTradeSignal` | 有需求时先设计输入和对齐契约 |

Signal 只能使用当前及以前的数据。Outcome 的 `n_forward` 是固定后续观测数，`result_index` 是结果所属锚点；不要将回填结果当作锚点当时可用的信息。单 K 线和 Bundle 分别放在并列的 `sigma2/kline/`、`sigma2/kline_bundle/`。

Bundle 算子持有固定 `symbols` 轴；一份快照缺少某个 symbol 仍推进共同时间。横截面计算可直接继承 Bundle family；逐 symbol 复用已有实现时使用 `rKlineBundleMapSignal` 或 `rKlineBundleMapOutcome`，每个 symbol 有独立子状态。

## 实现约定

- 直接使用 pyta2 的 `Schema`、`Space` 声明 schema，例如 `Scalar(low=-np.inf, high=np.inf, dtype=np.float64)`；一个 Bundle Space 描述一个 symbol。单字段返回数组，多字段按 schema 顺序返回 tuple，或返回 schema key 到值的 mapping。
- 按算法声明 `n_backward` 和 `n_forward`；需要历史字段时另显式声明 `history_window`，它不等同于 `min_periods`。窗口 family 的 `forward` 接收 OHLCV 数组，单 K 线是一维，Bundle 是 `(时间, symbol)`。
- 实现 `forward()`、`full_name` 和必要的 `reset_extras()` 或 `reset_window_extras()`。不要手动修改 `g_index` 或输出缓存。计算失败后状态可能已改变，应 `reset()` 并重放。
- 复用 pyta2 时参考 `_rKlineIndicatorFactor`，确认上游指标已迁移且支持有限历史；通用桥接须显式指定历史长度。不要假定所有指标都能仅用 `min_periods` 的有限窗口重算。
- 对外稳定算子可以配对 batch 函数：Signal 用 `forward_signal_apply()`，Outcome 用 `forward_outcome_apply()`，不要维护第二套计算公式。结果列以 `factor_names` 标识，实际参数应进入 `full_name`。
- 将新实现放在相应数据目录的领域子目录，更新领域和必要的根包导出。检查数据时点、缺失、symbol 轴、预热、状态重置以及 batch 与在线的对齐；执行范围以用户要求和仓库指令为准。
