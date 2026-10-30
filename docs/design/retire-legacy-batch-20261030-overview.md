# 旧 batch 与遗留依赖清理设计

> 此后已按新契约重建 Bundle Signal 和收益率排名，见 [K 线截面收益率排名设计](kline-bundle-return-rank-20261030-overview.md)。旧实现仍保留在备份中。

## 背景

目前单 K 线、盘口、成交的批量入口已统一使用 `forward_step_apply`；旧 `sigma2.batch` 仍依赖 `return_dict`、`step_input_keys`、`missing_output`、`factor_names` 等已移除的 core 约定。旧 Bundle 也依赖这套约定，并继续引用旧 K 线输入适配。用户明确不要求兼容。

## 方案比较

| 方案 | 结果 | 决定 |
| --- | --- | --- |
| 只移除旧 batch，保留 Bundle 原文件 | Bundle 的几个模块仍直接导入已删除的 batch，留下断开的入口 | 不采用。 |
| 同时迁移 Bundle | 能恢复截面功能，但需要先定义每个 symbol 的输出、缓存和批量形状，超出本轮清理范围 | 不在本轮实施。 |
| 归档旧 batch、旧 Bundle 及仅为其服务的辅助实现 | 当前包只保留已迁移接口；历史实现仍可作为后续重新设计的参考 | 采用。 |

## 清理范围

- `sigma2/batch.py`，以及顶层 `forward_signal_apply`、`forward_outcome_apply` 导出。当前单 K 线、盘口和成交的批量重放保留 `forward_step_apply`。
- 未适配当前 core 的 `sigma2/kline_bundle` 整个旧实现及顶层导出。后续若需要 Bundle，按固定输入、字典输出和 core 生命周期重新设计，而不是保留不工作的旧公共接口。
- 仅服务于旧 Bundle 和旧 batch 的 `sigma2/kline/_internal`、`sigma2/kline/data.py`、`KlineBar` 导出，以及没有生产代码使用的 `core/identity.py` 和 `qualify_factor_name` 导出。
- 以上源码原样移至 `docs/backup/v-0.11`，目录结构保持来源可辨。现有历史文档作为当时的记录保留，当前 README 和使用指南更新为新的范围。

## 边界检查

1. 已迁移的算子、pyta2 桥接和示例不引用要归档的模块；保留 `sigma2/utils/pyta2.py` 和 core 的 pyta2 组件，它们仍有实际调用。
2. 旧 Bundle 按 symbol 输出数组；当前 `forward_step_apply` 的声明 schema 表格收集面向标量，不宣称已支持 Bundle 批量输出。重建 Bundle 时需另定输出和缓存契约。
3. 旧测试仍引用旧接口，且本轮按用户要求不编写或运行测试；原测试保留，后续需要按新契约处理，不用恢复过时实现来满足它们。
