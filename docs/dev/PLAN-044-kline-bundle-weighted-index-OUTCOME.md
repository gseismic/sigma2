# PLAN-044：实施结果

- 完成时间：2026-10-30 06:50 CST
- 计划：`docs/dev/PLAN-044-kline-bundle-weighted-index.md`
- 设计：`docs/design/kline-bundle-weighted-index-20261030-overview.md`

## 结果

- 实现 `rKlineBundleWeightedIndex`：通过构造参数指定固定权重，或按每个截面 `bundle` 中各 symbol 的 `market_cap` 动态加权；根据用户确认，指数为当前价格的加权平均值。
- 固定权重在构造时归一化；正权重成分缺失则输出 NaN。市值模式对本次截面加权，市值未知、无效或正市值成分价格缺失时输出 NaN；`has_missing=True` 也输出 NaN，避免将缺失的成分默认为不存在。
- 两种模式沿用 `rKlineBundleSignal` 的固定签名和 core 生命周期；`used_fields` 根据构造参数包括所选价格字段，并在市值模式额外包括 `market_cap`。提供批量入口及公共导出。
- 更新 README 和使用指南，增加自包含示例 `examples/402_bundle_weighted_index.py`。

## 审阅与检查

- 静态审阅固定权重复制与归一化、市值缩放、零权重、缺失、空截面、输出 schema 和批量重放。价格加权平均没有基点，市值与成分变化会影响结果；市值与价格的时间匹配由上游保证。
- `ruff check sigma2 examples`、`ruff format --check sigma2 examples` 和 `git diff --check` 通过；静态搜索确认 core 未引入市场数据模块，示例未依赖 `_data`。
- 按用户要求，未编写或运行测试，也未运行示例；实际运行行为仍待验证。改动与此前的旧接口归档及截面排名一并保留在工作区供审阅，未提交。
