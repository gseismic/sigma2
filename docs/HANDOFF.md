# sigma2 交接文档

更新时间：2026-07-04 13:29 CST

## 项目背景

sigma2 是计划中的量化 ML 信号与特征生成库。核心使用场景是机器学习方法开发交易策略：用户用历史数据批量生成训练矩阵，并在回测或实盘中用同一组信号在线更新。sigma2 可以组合 pyta2 rolling 指标，也可以适配 minbt，但不应只是 pyta2 封装或 minbt 附属。

当前项目仍处于初始化规划阶段，尚未实现 Python 包代码。

## 当前仓库状态

- 当前仓库目录：`/Users/mac/pai-studio-fin/library/sigma2`
- 当前分支：`main`
- 已跟踪文件原本只有 `.gitignore` 和 `AGENTS.md`。
- `pyta2` 是指向 `../pyta2` 的软链接，当前为未跟踪状态，只作为本次规划参考。
- 本次新增文档均位于仓库自身目录，不依赖提交 `pyta2` 软链接。

## 本次完成工作

- 阅读 `pyta2/docs/design/pyta2-sigma-20260627-v3.md`。
- 抽查 pyta2 实现，确认 `rIndicator` 已提供 `output_keys`、`schema`、`required_window`、`meta_info`。
- 确认 `rATR`、`rMACD`、`rSMA` 的真实输入签名、输出和窗口形态。
- 创建 `README.md`。
- 创建 `docs/design/sigma2-20260704-roadmap.md`。
- 创建 `docs/dev/PLAN-001-sigma2-roadmap.md`。
- 创建 `docs/dev/PLAN-001-sigma2-roadmap-OUTCOME.md`。
- 创建 `docs/dev/INDEX.md`。
- 根据用户反馈新增 `docs/design/sigma2-20260704-signal-core.md`。
- 新增 `docs/dev/PLAN-002-signal-core-revision.md` 和结果文件。
- 更新 README、roadmap、INDEX 和交接文档，修正核心方向。
- 根据进一步反馈补充 data-kind 分层：`rSignal` 不锁死 K 线输入，K 线由 `rKlineSignal` 承担，未来 orderbook/trades 用对应子类扩展。
- 根据最新讨论新增 `docs/design/sigma2-20260704-system-design.md`。
- 新增 `docs/dev/PLAN-003-system-design.md` 和结果文件。
- 更新计划索引和交接文档，明确 ML 主路径与内部输入对象边界。

## 核心结论

- 用户主入口应是 `FeatureSet.batch(data)` 和 `FeatureSet.online()`。
- 普通用户不应手写 `KlineInput`、`OrderBookInput` 等内部标准化对象。
- `rSignal` 中 `r` 表示 rolling，是有状态内核，区别于 batch 特征生成主入口。
- Signal family 由输入类型决定，单 symbol 与多 symbol 要分开：`kline`、`multi_kline`、`orderbook`、`multi_orderbook`、`trade`、`multi_trade`、`composite`、`label`。
- batch 是 sigma2 的核心场景，不是 online replay 的附属接口；第一版可用 replay 实现，但接口上必须是一等能力。
- minbt 只作为 adapter，sigma2 核心命名使用 `kline/orderbook/trade/news`。
- pyta2 指标通过适配层接入 kline rolling 信号，sigma2 不重复维护 pyta2 指标定义。

## 重要文档

- `README.md`
- `docs/design/sigma2-20260704-system-design.md`
- `docs/design/sigma2-20260704-roadmap.md`
- `docs/design/sigma2-20260704-signal-core.md`
- `docs/dev/PLAN-001-sigma2-roadmap.md`
- `docs/dev/PLAN-002-signal-core-revision.md`
- `docs/dev/PLAN-003-system-design.md`
- `docs/dev/INDEX.md`
- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`

## 建议下一步

优先按 `docs/design/sigma2-20260704-system-design.md` 实施最小主路径：

1. 创建 Python 包骨架和测试框架。
2. 实现 `FeatureSet.batch(data)` 的最小 kline DataFrame 路径。
3. 实现 `DataSchema` 自动推断和显式字段映射。
4. 实现 `rSignal`、`rKlineSignal` rolling 内核，服务 batch 与 online。
5. 实现 `kline.ret`、`kline.sma`。
6. 实现 `FeatureSet.online()` 和 `update_kline(...)`。
7. 再扩展 orderbook/trade、pyta2 adapter、minbt adapter、composite 和 label。

不要先要求用户构造内部输入对象，也不要先做复杂 DAG、batch 向量化优化或 minbt 深度集成。
