# sigma2 交接文档

更新时间：2026-09-22 18:06 CST

## 项目背景

sigma2 是量化 rolling signal 与 ML 特征生成库。当前核心定位是类似 `pyta2.base.rIndicator` 的轻量继承式信号体系：用户直接继承 `rSignal` / family 子类定义信号，再由未来的 batch、online、minbt 或 ML 应用层消费这些信号。

最新 v5 设计进一步明确：pyta2 提供基础 rolling 计算积木；sigma2 负责把 kline、orderbook、trade 等市场事件、一个或多个 pyta2 指标和自定义逻辑组合成独立 Signal。pyta2 直接转 Signal 只保留一个薄桥接器，不再扩展 `rPyta2Xxx` 镜像 catalogue。每个公开 Signal 原则上独立文件。

面向真实量化研究、深度学习和强化学习训练，应用层中心仍采用 `FeatureData -> TargetData -> ResearchDataset -> AnalysisReport / EnvBuilder`；这些能力消费 Signal，不进入 sigma2 core。

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
- 当前总设计：`docs/design/sigma2-20260922-v5.md`。
- v5 是已完成的设计稿，尚未实施；当前源码仍是 v0.1 基线。
- `docs/design/sigma2-20260704-overview.md` 已被 v5 替代，只作为当前代码的历史设计依据。
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

## 最新设计结论与实现差异

- `step()` 仍是唯一推进到新逻辑观测的方法。
- v5 新增 `update_last()` 设计：修订最后一条观测，不推进 `g_index`，只覆盖最后输出；当前 sigma2 代码尚未实现。
- `forward()` 是计算 hook，不负责 core 生命周期；它可以修改算法私有递推状态，因此 runner 不能直接调用。
- `rSignal` 不固定 OHLCV；K 线、orderbook、trade 由各自 family 定义单条观测输入。
- `rKlineWindowSignal` opt-in 维护 OHLCV 历史窗口；v5 要求 update-last 时只替换窗口最后一行。
- pyta2 已经拥有 schema、full name、window、registry、`rolling()` 和正在实现的 `update_last()`；sigma2 不重复定义这些内容。
- v5 只保留一个通用 pyta2 bridge。当前 `rPyta2Signal` 可作为兼容名，`rPyta2SMA` 保留一个 minor 周期后退出推荐路径。
- sigma2 的主要产物是独立的复杂 Signal，例如均值的均值、盘口 mid-price 均值和滚动成交失衡，而不是 pyta2 wrapper catalogue。
- `FeatureSet`、DataFrame batch、ML matrix builder、minbt adapter、因子分析、深度学习数据集和强化学习环境仍不属于 core。
- finalized runner 继续只依赖 `SignalLike.reset()/step()`；在线修订使用扩展的 `RevisableSignalLike.update_last()`。

## 重要文档

- `README.md`
- `docs/design/sigma2-20260922-v5.md`
- `docs/design/sigma2-20260704-overview.md`（历史）
- `docs/dev/PLAN-010-core-only-package-structure.md`
- `docs/dev/PLAN-010-core-only-package-structure-OUTCOME.md`
- `docs/dev/INDEX.md`
- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`

## 建议下一步

1. 单独制定计划，实现 `rSignal.update_last()`、family 同签名接口和状态检查点。
2. 将 `rPyta2Signal` 收敛为唯一薄 bridge，直接复用 pyta2 schema/full name/window/registry，并停止扩展 `rPyta2Xxx`。
3. 分别实现 `kline/mean_of_mean.py`、`orderbook/smoothed_depth_imbalance.py`、`trade/rolling_trade_imbalance.py`，验证三个 family 的组合模型。
4. 完成 append/revise 与最终序列 replay 一致性、窗口推导和 bridge metadata contract tests。
5. 上述核心稳定后，再实现 signal runner / `make_features()` 和研究训练层。
6. 明确 pyta2 的正式依赖或安装方式，替换当前本地软链接开发兜底。

不要先做全面 pyta2 wrapper catalogue、通用表达式 DAG、batch 向量化优化、minbt 深度集成、完整 RL 环境或自动模型训练框架。
