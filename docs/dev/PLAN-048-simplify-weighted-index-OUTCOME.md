# PLAN-048：实施结果

- 完成时间：2026-10-30 15:34 CST
- 计划：`docs/dev/PLAN-048-simplify-weighted-index.md`
- 设计：`docs/design/kline-bundle-weighted-index-20261030-overview.md`

## 结果

- 将原先通过参数选择模式的算子拆成 `rKlineBundleFixedWeightIndex` 和 `rKlineBundleMarketCapWeightedIndex`，分别在类文档中说明计算公式、输入及缺失规则。
- 增加对应的批量入口和公开导出；不保留原先的 `rKlineBundleWeightedIndex` 和 `KlineBundleWeightedIndex`。
- `has_missing=False` 时信任上游的输入，不逐项检查价格、市值或缺失标志。`has_missing=True` 时，固定权重类检查实际参与成分；市值加权类返回 NaN。市值全为零或截面为空时也返回 NaN。
- 归一化前按原始权重确定固定成分，避免极小正权重下溢后丢失成分及其缺失检查；极端比例下数值贡献仍可能下溢。
- 同步 README、使用说明和独立示例，示例展示非固定成分缺失对两种指数的不同影响。

## 审阅与检查

- 静态审阅两个算子的公式、输入契约、零权重、缺失标志、schema、元信息及批量导出。
- `ruff check sigma2 examples`、`ruff format --check sigma2 examples` 和 `git diff --check` 通过；静态搜索确认当前代码、示例和使用文档不再引用旧加权指数名称。
- 按用户要求，未编写或运行测试，也未运行示例；未提交。
