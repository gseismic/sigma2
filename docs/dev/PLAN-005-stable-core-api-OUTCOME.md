# PLAN-005 稳定核心 API 设计结果

更新时间：2026-07-04 16:31 CST

## 完成内容

- 新增并整理当前设计总文档 `docs/design/sigma2-20260704-overview.md`，把 `rSignal` / `rKlineSignal` 定义为 sigma2 最稳定核心。
- 根据用户补充要求，明确 `rSignal` 在概念、命名、生命周期和默认行为上尽可能保持 `pyta2.base.rIndicator` 一致。
- 明确 `FeatureSet`、DataFrame batch、online state、minbt adapter 属于应用层或适配层，不再作为 core 的定义中心。
- 确定稳定核心接口包含生命周期、schema、输出、缓存、`g_index`、`return_dict`、`meta_info`、`family`、`rolling()`、`update()`、`forward()`。
- 冻结 `rKlineSignal` 的 K 线输入契约：rolling 输入 `opens, highs, lows, closes, volumes`，update 输入 `open, high, low, close, volume`。
- 将 `rolling()` 定位为与 `rIndicator` 对齐的主生命周期入口；`update()` 在 base 层最多是 `rolling()` 的兼容别名，在 family 子类才表达单点行情输入，且必须委托 `rolling()` 的生命周期。
- 将 `data_kind` 下调为旧文档术语或内部兼容别名，公共稳定命名采用 `family`。
- 给出 orderbook/trade 的扩展原则和候选输入契约，避免在真实信号不足前过早冻结复杂行情细节。
- 增加 v0 阶段兼容规则和 contract tests 要求。
- 更新旧系统设计状态并在后续整理中移入 `docs/design/backup/`，标记其应用层内容仅保留历史价值；当前 core 以 overview 文档为准。
- 更新 README、交接文档和计划索引。

## 结论

sigma2 后续应按 core-first 实施：

```text
rSignal -> rKlineSignal -> concrete signals -> pyta2 adapter -> SignalEngine -> FeatureSet/app
```

不应按 app-first 实施：

```text
FeatureSet -> hidden signal objects
```

这样用户可以马上继承 `rKlineSignal` 写信号，并在后续 `FeatureSet`、minbt、ML batch API 变化时保持信号类稳定可用。
