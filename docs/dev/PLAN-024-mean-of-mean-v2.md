# PLAN-024：基于 pyta2 MA 的两级均值 V2

更新时间：2026-09-24 16:50 CST

状态：已实施，结果见 `PLAN-024-mean-of-mean-v2-OUTCOME.md`

## 目标

保留已实现的纯自算两级均值 V1，新增 V2，使用 pyta2 MA 模块计算两层均值，并允许选择 MA 类型。设计依据：`docs/design/mean-of-mean-v2-20260924-template.md`。

## 实施步骤

1. 按 `docs/design/pyta2-composition-api-20260924-overview.md` 将 core 的 pyta2 专属调用入口改为通用的 `apply_component()`，保留公开的 `checkpoint_fields`；在 `sigma2.utils.pyta2` 添加 pyta2 适配对象，迁移仓库内旧调用方和测试。
2. 在 `sigma2/kline/trend/mean_of_mean_v2.py` 实现配对 rolling/batch API；用两个 pyta2 MA 组件、两个轻量适配对象和一个有界中间 deque 管理新增与末根修订。
3. 按两个组件的 `required_window` 计算真实预热长度，明确 full name、字段绑定与高级参数校验。
4. 保留 V1 文件、导出与行为；新增 V2 导出、示例和文档。
5. 验证八种 MA 类型、SMA 对 V1、KAMA 高级参数、连续修订、续写、batch 与独立 pyta2 计算一致；验证通用组件入口的生命周期、错误和非 pyta2 组件。审阅后写 OUTCOME、追加 INDEX，只提交本计划文件并立即推送。

## 完成标准

- V1 公共接口、数值及文件未改动；V2 可通过 `ma_type` 选择 pyta2 MA。
- V2 的预热、训练列身份、batch 和在线修订行为与组件真实语义一致。
- `rSignal` 中没有 `_apply_pyta2()`、`apply_pyta2()` 或 `rIndicator` 类型依赖；V2 不调用受保护桥接；组件桥接和自有状态声明均有公开作者接口。
- 全套既有测试及新增契约测试通过；用户未跟踪文件不进入提交。
