# PLAN-037：实施结果

- 完成时间：2026-10-30 05:46 CST
- 计划：`docs/dev/PLAN-037-kline-macd.md`
- 设计：`docs/design/kline-macd-20261030-overview.md`

## 结果

- `rKlineMACD` 直接继承 `rKlineSignal`，只保存一个 pyta2 `rMACD` 和一个所选字段窗口；快照、重算和重置由 core 负责。
- 保留 `fast`、`slow`、`signal` 和 `field` 参数，将周期显式映射到 pyta2 的 `n2`、`n1`、`n3`；实例的 `used_fields` 由所选字段确定。
- 启用 pyta2 的字典输出，复用其 `dif`、`dea`、`macd` schema、预热及缺失值处理。`volume=None` 按缺失值输入。
- 移除旧 `KlineMACD` 批量函数及直接导出；更新 README，其他指标和通用 batch 尚未迁移。

## 审阅与检查

- 静态审阅了所固定 pyta2 版本的 MACD 参数顺序、输出字段、内部 EMA 及 DIF 缓存、`return_dict` 路径和预热定义；也审阅了快照与重置的状态归属。
- `ruff check`、`ruff format --check` 和 `git diff --check` 通过。
- 按用户此前要求未编写或运行测试。盘中更新、缺失恢复、深复制与计算结果仍需后续运行验证；实施时未提交，用户随后要求提交。
