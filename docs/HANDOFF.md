# sigma2 交接文档

更新时间：2026-07-07 12:01 CST

## 项目背景

sigma2 是量化 rolling signal 与 ML 特征生成库。当前核心定位是类似 `pyta2.base.rIndicator` 的轻量继承式信号体系：用户直接继承 `rSignal` / family 子类定义信号，再由未来的 batch、online、minbt 或 ML 应用层消费这些信号。

当前结构已经迁移为 core-only：

- `sigma2/core/`：唯一核心目录，包含 `rSignal`、K 线/orderbook/trade family 基类、`rPyta2Signal`。
- `sigma2/kline/`：K 线具体信号，每个信号一个文件。
- `sigma2/orderbook/`：订单簿具体信号。
- `sigma2/trade/`：逐笔成交具体信号。
- `sigma2/utils/`：pyta2 导入兼容、resolver、registry 等辅助能力。

不再保留 `base/`、`families/`、`signals/`、`adapters/` 作为公共源码结构。

## 当前仓库状态

- 当前仓库目录：`/Users/mac/pai-studio-fin/library/sigma2`
- 当前分支：`main`
- 当前唯一有效设计文档：`docs/design/sigma2-20260704-overview.md`
- `docs/design/backup/` 中的文档仅用于历史追溯，不作为当前实现依据。
- `pyta2` 是指向相邻仓库的软链接，当前为未跟踪状态，只作为设计、实现和测试参考；不要提交该软链接。
- `minbt` 是本地软链接，当前为未跟踪状态，只作为边界参考；不要提交该软链接。
- `AGENTS.md` 有用户侧修改，后续工作不要擅自回退。

## 已完成的当前实现

- 新增 `pyproject.toml`。
- 实现 `sigma2.core.rSignal`。
- 实现 `sigma2.core.rKlineSignal`、`rKlineWindowSignal`、`rOrderBookSignal`、`rTradeSignal`。
- 实现 `sigma2.core.rPyta2Signal` 和 `pyta2_signal()`。
- 实现 `sigma2.utils.pyta2.ensure_pyta2_importable()`、`resolve_pyta2_indicator()`、`register_pyta2_indicator()`。
- 实现根级信号分类：
  - `sigma2.kline.rReturn`
  - `sigma2.kline.rGap`
  - `sigma2.kline.rSMA`
  - `sigma2.kline.pyta2.rPyta2SMA`
  - `sigma2.orderbook.rBookSpread`
  - `sigma2.trade.rTradeSignedVolume`
- 增加新结构 contract tests，覆盖 `sigma2.core`、`sigma2.kline`、`sigma2.orderbook`、`sigma2.trade`、`sigma2.utils.pyta2` 导入路径。

## 核心结论

- `step()` 是唯一公共状态推进入口。
- `forward()` 是计算 hook，直接调用不推进状态。
- `window` 表示产生有效输出所需最少 step 数，不表示 core 默认维护原始输入历史。
- `rKlineSignal` 不默认维护 OHLCV 历史。
- `rKlineWindowSignal` opt-in 维护 OHLCV 历史窗口，内部使用 pyta2 的 `DequeTable`。
- orderbook/trade family 默认不维护输入历史窗口。
- pyta2 是适配来源，不是 sigma2 core；当前只保留 `rPyta2SMA` 作为类式快捷适配样例，不做全面 catalog 迁移。
- `FeatureSet`、DataFrame batch、ML matrix builder、minbt adapter 尚未实现，后续应作为 core 消费者。

## 重要文档

- `README.md`
- `docs/design/sigma2-20260704-overview.md`
- `docs/dev/PLAN-010-core-only-package-structure.md`
- `docs/dev/PLAN-010-core-only-package-structure-OUTCOME.md`
- `docs/dev/INDEX.md`
- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`

## 建议下一步

1. 实现最小 `SignalEngine`，只消费 `rSignal.step()`，不反向污染 signal 类。
2. 实现 `FeatureSet` 的 batch replay 原型和 ML matrix builder。
3. 根据真实使用扩展 orderbook/trade 的更多内置信号和 contract tests。
4. core 和应用层稳定后再实现 minbt adapter。
5. 明确 pyta2 的正式依赖或安装方式，替换当前本地软链接开发兜底。

不要先做全面 pyta2 指标迁移、复杂 DAG、batch 向量化优化、minbt 深度集成或同周期 update/rollback。
