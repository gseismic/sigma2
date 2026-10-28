---
name: sigma2-usage
description: 当用户询问安装或使用 sigma2、计算单 K 线或多 symbol 截面因子、推进 Signal/Outcome、使用批量结果，或要扩展 sigma2 算子时使用。提供符合当前源码的示例和扩展指引。
---

# sigma2 使用与扩展

先读仓库根目录 `README.md`、`sigma2/__init__.py` 和目标类源码；源码和实际导出优先于历史设计。当前接口以 [Operator 设计](../../docs/design/sigma2-operator-signal-outcome-20261028-overview.md)和 [KlineBundle 设计](../../docs/design/kline-bundle-20261028-overview.md)为依据。新增算子时再读[扩展指南](references/add-signals.md)。

| 任务 | 示例 |
| --- | --- |
| 单 symbol K 线批量、在线或重放 | [批量](../../examples/01_kline_batch.py)、[在线](../../examples/02_kline_stream.py) |
| 盘口快照和逐笔成交 | [市场事件](../../examples/03_market_events.py) |
| 未来结果及锚点位置 | [未来 Outcome](../../examples/04_future_outcome.py) |
| 调用 pyta2 或编写自定义 Signal | [pyta2 桥接](../../examples/05_pyta2_bridge.py)、[自定义 Signal](../../examples/06_custom_signal.py) |
| 自有或 pyta2 指标组合 | [均值组合](../../examples/07_mean_of_mean.py)、[均值组合 V2](../../examples/08_mean_of_mean_v2.py) |
| 多 symbol 截面、缺失和未来结果 | [KlineBundle](../../examples/09_kline_bundle.py) |

## 关键使用契约

- 单 symbol 流使用 `sigma2.kline.KlineBar` 和 `rKlineX.step(bar)`；多 symbol 同时点快照使用 `sigma2.kline_bundle.KlineBundle` 和 `rKlineBundleX.step(bundle)`。每个 Bundle 固定 symbol 顺序；没有 Bar 的 symbol 从 `bars` 省略。盘口和成交保留各自的事件输入。
- `rSignal` 的输出属于当前观测；`rOutcome` 等待固定未来期，输出属于 `result_index = g_index - n_forward`。`n_forward` 是输入次数，不自动等于自然日。回填到历史锚点不代表当时已知；说明数据的 `available_at` 和计算发布延迟。
- 批量使用具名函数或 `forward_signal_apply()` / `forward_outcome_apply()`，按输入顺序重放；Outcome 结果按锚点回填。Bundle 的字段数组形状为 `(时间, symbol, *space.shape)`，输出列名由 `factor_names` 决定。
- `schema` 使用 pyta2 的 `Schema` / `Space`，Bundle 中一个 Space 描述一个 symbol。`return_dict=True` 的 key 来自 schema；输出缓存默认保存最近一步，`0` 关闭、`-1` 无限。修改历史或失败后 `reset()` 并从头重放。
- 通用 `pyta2_signal()` 需要显式 `history_window`，只适配支持有限历史窗口的指标；已有公开因子优先使用 `rKlineX` / `KlineX`。

回答使用问题时给出定义完整输入的代码，并说明预热、缺失及多 symbol 结果顺序。用户要求重新设计接口时，遵循仓库 `AGENTS.md` 使用 `api-design-zh`。
