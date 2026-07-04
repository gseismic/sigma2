# PLAN-003 执行结果：形成 sigma2 系统设计文档

完成时间：2026-07-04 13:29 CST

## 完成内容

- 新增 `docs/design/sigma2-20260704-system-design.md`，作为当时推荐系统设计稿。该设计后续已移入 `docs/design/backup/sigma2-20260704-system-design.md`，当前实现依据见 `docs/design/sigma2-20260704-overview.md`。
- 文档明确 `FeatureSet.batch(data)` 和 `FeatureSet.online()` 是用户主路径。
- 文档明确 `KlineInput`、`OrderBookInput`、`TradeInput` 是内部标准化对象或高级接口，不要求普通用户手写。
- 文档明确 `rSignal` 中 `r` 表示 rolling，是有状态内核，区别于 batch 特征生成主入口。
- 文档明确 signal family：`kline`、`multi_kline`、`orderbook`、`multi_orderbook`、`trade`、`multi_trade`、`composite`、`label`。
- 文档明确 minbt 只在 adapter 边界出现，sigma2 核心使用 `kline/orderbook/trade/news`。
- 更新 `docs/dev/INDEX.md` 和 `docs/HANDOFF.md`。

## 未完成内容

- 未实现 Python 包代码。
- 未修改 minbt 或 pyta2。
- 未提交 `minbt`、`pyta2` 软链接。
- 未处理工作区中既有的 `AGENTS.md` 修改。

## 结论

后续实现应从 `FeatureSet.batch(data)` 的最小 kline 路径开始，而不是先要求用户构造内部输入对象。`rSignal`、`rKlineSignal` 等 rolling 内核应服务于 batch 与 online 两条主路径。
