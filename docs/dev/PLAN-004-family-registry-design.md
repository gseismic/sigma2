# PLAN-004：补充输入类型驱动的 family 扩展设计

更新时间：2026-07-04 15:50 CST

## 背景

用户强调：按数据输入类型定义 signal family 是二次开发的关键。新增数据类型时，应该增加 `InputType + family + normalizer + signals`，而不是修改核心流程。同时，之前系统设计稿中 `update_minbt_bars(...)` 示例会污染 sigma2 core API，需要修正为 adapter 边界。

## 目标

- 将“输入类型决定 family”升级为系统设计硬规则。
- 增加 `FamilyRegistry` 设计，保证新增 family 不需要修改 `FeatureSet` / `OnlineFeatureState` 核心逻辑。
- 明确 `update(input_obj)`、`update_family(family, **data)` 是在线核心扩展接口。
- 明确 `update_kline(...)` 是便捷接口，不是扩展机制本身。
- 修正 minbt 示例，避免 `update_minbt_bars(...)` 出现在 core 对象。

## 范围

包含：

- 更新 `docs/design/sigma2-20260704-system-design.md`。
- 新增本计划结果文件。
- 更新 `docs/dev/INDEX.md`。
- 更新 `docs/HANDOFF.md`。

不包含：

- 实现 Python 代码。
- 修改 minbt 或 pyta2。
- 提交未跟踪软链接。
- 处理既有 `AGENTS.md` 修改。

## 验收标准

- 文档明确 `InputType -> SignalFamily -> Signal`。
- 文档明确 family 通过 registry 扩展。
- 文档明确新增数据类型不应修改核心类。
- 文档明确 minbt 只在 `sigma2.adapters.minbt` 边界出现。
- 文档删除 core 对象上的 `update_minbt_bars(...)` 示例。
