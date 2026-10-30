---
name: sigma2-usage
description: 回答 sigma2 的安装、单 K 线、截面收益率排名与加权价格指数、盘口和成交算子、批量重放、未来结果及自定义算子问题，并引用当前源码和示例。
---

# sigma2 使用与扩展

先读仓库根目录 `README.md`、`sigma2/__init__.py` 和目标类源码；源码和实际导出优先于历史设计。新增算子时再读[扩展指南](references/add-signals.md)。

| 任务 | 示例 |
| --- | --- |
| 均线在线、盘中更新与批量 | [均线](../../examples/001_kline_ma.py) |
| 其他 K 线指标 | [趋势](../../examples/002_kline_trend.py)、[动量](../../examples/003_kline_momentum.py)、[波动](../../examples/004_kline_volatility.py)、[量价](../../examples/005_kline_volume.py) |
| pyta2 桥接 | [pyta2 桥接](../../examples/006_kline_pyta2.py) |
| 价格变化和缺失数据 | [价格](../../examples/007_kline_price.py)、[缺失](../../examples/008_kline_missing.py) |
| K 线截面收益率排名 | [收益率排名](../../examples/401_bundle_return_rank.py) |
| K 线截面加权价格指数 | [加权指数](../../examples/402_bundle_weighted_index.py) |
| 盘口和成交 | [盘口](../../examples/101_orderbook_spread.py)、[成交](../../examples/201_trade_signed_volume.py) |
| 自定义有状态信号 | [成交信号](../../examples/202_trade_custom_signal.py) |
| 未来结果与锚点 | [未来收益](../../examples/301_outcome_return.py)、[ATR 边界](../../examples/302_outcome_atr_bound.py) |

## 关键使用契约

- 单 K 线使用 `step(open, high, low, close, volume=None, *, open_time=None, is_closed=True, is_missing=False)`，输入格式由上游保证。未结束 K 线可多次更新并最终确认；有 `open_time` 时 core 会检查观测身份。
- K 线截面使用 `step(bundle, *, open_time=None, has_missing=False)`；`rKlineBundleReturnRank(lag=1)` 按 `close_t / close_(t-lag) - 1` 升序稳定排名，输出 `{"rank": {symbol: rank}}`；相同收益率按当前 Bundle 的输入顺序分配不同名次。历史不足、端点价格缺失或参考价格为零时为 NaN；每次 step 推进共同时间位置。
- 单周期技术指标使用 `n`；`rKlineReturn` 和截面收益率排名使用 `lag` 表示参考观测相隔的逻辑步数。`n_backward`、`n_forward` 描述时序依赖，`history_window` 和 `buffer_size` 分别表示输入历史与输出缓存。
- `rKlineBundleFixedWeightIndex(weights)` 使用固定成分权重；`rKlineBundleMarketCapWeightedIndex()` 使用当前 Bundle 各 symbol 的 `market_cap`。输出 `{"index": ...}`，是价格加权平均值，不是基点收益指数。`has_missing=False` 由调用方保证参与数据完整有效，算子不逐项校验；`has_missing=True` 时，固定模式仅在实际成分缺失或价格无效时返回 NaN，市值模式直接返回 NaN。
- 盘口使用 `step(*, bids, asks)`，成交使用 `step(*, price, volume, side=None)`。所有 `step` 和 `forward` 都返回字典；`used_fields` 是实例元信息，不参与逐条校验。
- `n_backward` 是结果位置之前的最少观测数，`min_periods = n_backward + 1 + n_forward`。递推算法的最少预热不保证与更早开始持续运行的状态一致。
- `rSignal` 的结果属于当前观测；`rOutcome` 等待固定后续观测，结果属于 `result_index = g_index - n_forward`。未来结果回填历史锚点不代表锚点时已经可用。
- 批量函数及 `forward_step_apply(data, operator)` 按固定字段字典逐条重放，返回 schema 键；未结束观测的更新只占一行，Outcome 回填锚点，尾部未成熟位置使用 schema 缺失值。继续已有状态时，返回表只包含本次输入的观测。
- `schema` 使用 pyta2 的 `Space`，可省略；缓存默认保存最近一步，`0` 关闭，`-1` 无限。计算失败后 `reset()` 并重放。自定义算子的可变状态必须通过 `_state` 保存和读取，才能重算与重置。
- `pyta2_signal()` 需要显式 `history_window`，调用者应确认指标支持有限历史。MA 及使用 MA 的指标只支持单周期类型；缺失值后的行为由 pyta2 决定。
- 旧 `kline_bundle`、`sigma2.batch` 及相关示例已归档。当前 Bundle 提供 Signal 基类、收益率排名和加权价格指数；不要把历史文档当成当前接口。

回答使用问题时给出完整输入，并说明相关的预热、缺失和未来结果可用时间。用户要求重新设计接口时，遵循仓库 `AGENTS.md` 使用 `api-design-zh`。
