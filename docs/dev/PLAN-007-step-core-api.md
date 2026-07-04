# PLAN-007 step 核心接口修订

更新时间：2026-07-04 17:07 CST

## 背景

用户进一步指出：K 线以外的 orderbook、trades 等输入不一定需要维护历史 window。如果继续把 `rolling()` 或 `update()` 作为核心公共入口，会把 K 线窗口型指标的心智强加给所有 family，并且容易让用户交替调用 `update()`、`rolling()`、`forward()` 导致状态不一致。

同时，用户认可 `forward()` 作为类似神经网络 forward 的子类计算方法名，但希望用户正常只有一个入库入口。

## 目标

- 将 sigma2 core 的唯一公共状态推进入口确定为 `step()`。
- 保留 `forward()` 作为子类实现 hook，但明确直接调用不进入 core 生命周期。
- 从当前设计中移除 `rolling()` 和 `update()` 作为 core 稳定接口。
- 明确 `window` 表示有效输出所需最少 step 数，不等于默认维护原始输入历史。
- 新增 `rKlineWindowSignal` 概念，让需要 OHLCV 历史序列的 K 线信号 opt-in 维护窗口；窗口维护发生在 `step()` 调用链内部。
- 明确同周期 K 线修正、未完成 K 线预览、盘口 delta 等属于 adapter / stream builder / preview runner 责任，不进入 `rSignal` core。
- 同步 README、交接文档和计划索引，避免文档误导实现。

## 设计判断

采用 `step()` 作为唯一公共入口，原因：

- `step()` 对 kline、orderbook、trade、funding rate、news 等 family 都表示“输入流推进一个新观测点或事件”。
- `update()` 在 orderbook 语境中容易被理解为“应用盘口增量”，不适合作为通用信号推进方法。
- `rolling()` 暗示历史序列和窗口缓存，不适合 orderbook/trades 的高频事件流。
- `mode="append/update"` 这类参数会把“追加新事件”和“修正当前事件”混在一个入口里，迫使所有 signal 支持回滚或替换状态，复杂度过高。

## 修改范围

- `docs/design/sigma2-20260704-overview.md`
- `README.md`
- `docs/HANDOFF.md`
- `docs/dev/INDEX.md`
- 新增本计划结果文件

## 验收标准

- 当前唯一有效设计文档明确 `rSignal.step()` 是唯一状态推进入口。
- 当前唯一有效设计文档不再把 `rolling()` / `update()` 作为 core 稳定接口。
- K 线基础 family 与窗口型 K 线 family 分开。
- orderbook/trade 示例使用 `step()`，不默认维护历史窗口。
- README 和交接文档同步当前结论。
