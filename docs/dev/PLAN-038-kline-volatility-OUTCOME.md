# PLAN-038：实施结果

- 完成时间：2026-10-30 05:54 CST
- 计划：`docs/dev/PLAN-038-kline-volatility.md`
- 设计：`docs/design/kline-volatility-20261030-overview.md`

## 结果

- 删除 `mean_of_mean.py`、`mean_of_mean_v2.py` 和它们在 trend、kline 包中的导出。
- `rKlineATR` 直接组合 pyta2 ATR，状态包括一个指标和最近两根对齐的 HLC；均线类型与 MA 一致，`used_fields` 为 `high`、`low`、`close`。
- `rKlineBoll` 直接组合 pyta2 Boll，状态包括一个指标和所选字段的输入窗口；`used_fields` 根据 `field` 设置。
- 两者直接返回 pyta2 的字典和 schema，重算、确认和重置由 core 负责。移除了依赖未迁移 batch 的 `KlineATR`、`KlineBoll` 及其导出。
- 更新 README 和与已删除类直接相关的 skill 引用；保留原历史示例和测试，并明确它们尚未迁移。

## 审阅与检查

- 静态审阅固定版本 pyta2 的 ATR、Boll 输入、输出、公式名、参数与预热；ATR 只需最近两根 HLC，Boll 只需选定字段的预热窗口。
- `ruff check`、`ruff format --check`、`git diff --check` 通过。按用户此前要求未编写或运行测试，盘中重算、缺失恢复、深复制和计算结果仍需后续运行验证。
- 删除的两级均值类仍被历史示例和旧测试引用；这些文件未在本轮改写。其他指标、Outcome 和通用 batch 也尚未迁移。
- 实施时改动保留在工作区，未提交；保留之前尚未提交的 MACD 改动。用户随后要求提交。
