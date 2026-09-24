# PLAN-023：无 pyta2 指标的两级均值 Signal 模板

更新时间：2026-09-24 16:19 CST

状态：已完成

## 目标

在 `sigma2.kline.trend` 实现可扩展的 `rKlineMeanOfMean` / `KlineMeanOfMean`，让因子源码不使用 pyta2，借此验证 core 对自有状态修订与本地输出 schema 的支持。设计依据：`docs/design/mean-of-mean-20260924-template.md`。

## 实施步骤

1. 为 `rSignal` 增加 dtype 输出 schema 简写，保留现有 pyta2 `Schema`/`Space` 兼容性。
2. 实现两级简单移动均值 Signal、配对 batch 函数和 family 导出；两个有界 deque 使用 `_update_state_fields` 参与修订。
3. 增加可运行示例和扩展说明，测试窗口、字段、连续修订、重放、重置、batch 与旧 schema 兼容。
4. 审阅变更，运行测试与格式检查；写 OUTCOME、追加 INDEX，只提交本计划相关文件并立即推送。

## 完成标准

- 新 Signal 源码没有 pyta2 导入或指标调用，能以 `schema={"mean_of_mean": np.float64}` 构造。
- `required_window=inner_n+outer_n-1`，预热和非有限值处理与定义一致。
- `step()`、连续 `update_last()`、修订后续写、`reset()` 和 batch 结果与独立公式及最终数据重放一致。
- 旧 pyta2 因子与现有测试不回归；保留用户未跟踪文件原状。

## 执行摘要

- `rSignal` 接受 NumPy dtype 输出声明，旧 pyta2 `Schema`/`Space` 路径保持可用。
- `rKlineMeanOfMean` 自行计算两级简单均值，用两个有界 deque 保存状态，支持末根反复修订；`KlineMeanOfMean` 复用 core batch replay。
- 补充可运行示例、扩展指南、独立公式和生命周期测试；93 项测试通过。本次源码未导入 pyta2 指标，但 sigma2 core 的安装依赖仍包含 pyta2。
