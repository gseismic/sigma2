# 单 K 线波动指标精简设计

> 生命周期以[算子单向推进设计](operator-single-pass-20261031-overview.md)为准；本文保留当时的实现记录。

- 创建时间：2026-10-30 05:52 CST
- 范围：删除两个 `mean_of_mean` 指标和相关导出；改造单 K 线 ATR、Boll、直接导出与使用说明。
- 依据：`docs/design/kline-step-core-20261029-overview.md` 和 MA、MACD 的实现方式。

## 场景

1. 逐根输入 OHLCV，ATR 返回 `{"atr": ...}`，Boll 返回上、中、下轨字典。
2. 同一根未结束 K 线反复更新，最后确认；状态和输出缓存与最终输入重放一致。
3. ATR 使用 `high`、`low`、`close`；Boll 根据构造参数选择一个行情字段，并展示 `used_fields`。
4. 缺失 K 线或 Boll 的缺失 volume 交给 pyta2 计算；复位后可重新重放。
5. 用户了解 ATR 的均线类型、Boll 的窗口和倍数，以及由 pyta2 决定的预热长度。

## 方案

| 问题 | 方案 | 结论 |
| --- | --- | --- |
| 指标包装 | 继续使用 `_rKlineIndicatorFactor` | 依赖旧窗口和输入处理，不采用。 |
| 指标包装 | 直接继承 `rKlineSignal` 并持有 pyta2 指标 | 与 MA、MACD 一致，采用。 |
| ATR 输入 | 只给当前高低价和两根收盘价 | 目前公式足够，但传入序列长度不一致；不采用。 |
| ATR 输入 | 保存最近两根 HLC，提供对齐的三列 | 覆盖当前真实波幅所需的上一根收盘价，采用。 |
| Boll 输入 | 保存全部 OHLCV | 实际只使用一个字段，不采用。 |
| Boll 输入 | 保存选择的一个字段 | 输入窗口和 `used_fields` 均由实例配置决定，采用。 |
| 输出 | 在 sigma2 中手工映射 tuple | 重复维护 pyta2 的字段名；不采用。 |
| 输出 | 设置 pyta2 `return_dict=True` | 直接使用指标的 schema 和字典结果，采用。 |

## 契约

- `rKlineATR(n=20, *, ma_type="EMA", buffer_size=1)`：允许的均线与 `rKlineMA` 相同，只使用单周期参数；`used_fields=("high", "low", "close")`。指标和长度为 2 的 HLC 窗口保存在 `_state`，真实波幅、平滑、缺失行为和预热由 pyta2 决定。
- `rKlineBoll(n=20, F=2.0, *, field="close", buffer_size=1)`：保存一个 pyta2 指标和一个所选字段窗口；`used_fields=(field,)`，`volume=None` 按缺失数值处理。输出使用 pyta2 的 `ub`、`mid`、`lb`；参数校验和数值算法由 pyta2 负责。
- 两者将 `used_fields` 通过父类构造函数交给 core，并使用共同的 `step(open, high, low, close, volume=None, *, open_time=None, is_closed=True, is_missing=False)`。数据格式由上游保证；core 管理索引、缓存、确认、快照和重置。
- `full_name` 使用 pyta2 的公式名并附带实际字段，ATR 字段为 `[high,low,close]`，Boll 字段由 `field` 决定；不再另行规范化 Boll 倍数的文本表示。
- 删除 `mean_of_mean.py` 与 `mean_of_mean_v2.py` 及其导出。原示例和旧测试仍引用已删除的接口，暂不迁移，使用说明中标记为历史内容。
- 原 `KlineATR` 和 `KlineBoll` 使用未迁移的通用 batch；与 MA、MACD 一致，移除这两个批量入口及直接导出。

## 三轮检查

1. **输入**：ATR 的 HLC 三列始终对齐；Boll 只使用一个配置字段，`used_fields` 不参与逐条检查。
2. **状态与输出**：各类只有一个 pyta2 指标和一个窗口，均在 `_state`；schema 和字典键直接来自 pyta2。
3. **边界**：旧批量入口、已删除均值组合的示例和测试需后续处理；盘中更新的正确性依赖深复制，且需后续运行验证。
