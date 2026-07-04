# PLAN-002 执行结果：修正 sigma2 标准信号核心

完成时间：2026-07-04 12:11 CST

## 完成内容

- 新增 `docs/design/sigma2-20260704-signal-core.md`，定义通用 `rSignal`、K 线专属 `rKlineSignal`、标准 OHLCV 输入、标准输出、pyta2 适配和组合信号方向。
- 补充 data-kind 分层，明确 K 线不是唯一模型，未来 orderbook/trades 通过 `rOrderBookSignal`、`rTradeSignal` 等子类扩展。
- 更新 `README.md`，把项目定位从 pyta2 feature 编排层修正为自有标准信号计算库。
- 更新 `docs/design/sigma2-20260704-roadmap.md`，注明原 `FeatureSpec + Pyta2Adapter` 方向已降级为适配/配置细节。
- 更新 `docs/dev/INDEX.md`，追加本次计划和结果。
- 更新 `docs/HANDOFF.md`，记录用户反馈后的核心修正。

## 未完成内容

- 未实现 Python 包代码。
- 未创建 `pyproject.toml`。
- 未修改 pyta2。

## 结论

sigma2 后续应先实现通用 `rSignal`，再实现 `rKlineSignal` 和 `rPyta2Signal`。`FeatureSpec` 不应作为第一公共 API，而应后续作为声明式配置或矩阵输出层补充。orderbook/trades 不在第一阶段实现，但必须保留 data-kind 扩展口。
