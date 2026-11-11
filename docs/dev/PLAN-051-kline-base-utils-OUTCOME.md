# PLAN-051：实施结果

- 完成时间：2026-11-11 21:05 CST
- 计划：`docs/dev/PLAN-051-kline-base-utils.md`
- 设计：`docs/design/kline-package-layout-20261111-overview.md`

## 结果

- 将共享输入实现、`rKlineSignal` 和 `rKlineOutcome` 移至 `sigma2.kline.base`；两个基类继续共享同一个 `_KlineStep`，分别使用 core 的 Signal 和 Outcome 生命周期。
- 将 `rPyta2Signal` 和 `pyta2_signal` 移至 `sigma2.kline.utils`，继续使用 `sigma2.utils.pyta2` 中原有的指标注册表和 K 线字段规则。
- 更新 K 线具体指标和 Outcome 的基类导入；`sigma2`、`sigma2.kline` 与 `sigma2.kline.outcome` 的已有聚合名称保持可用，并新增 `sigma2.kline.base` 基类入口。
- 按用户选择移除旧 `sigma2.kline.signal`、`sigma2.kline.outcome_base` 和 `sigma2.kline.pyta2` 路径，不创建兼容转发；README 说明了直接导入及旧序列化数据的迁移影响。
- 其余数据类型、计算公式、固定 K 线输入、缺失值处理和算子生命周期未改动。

## 审阅与检查

- 审阅重命名差异：共享输入层及两种基类内容未变，桥接仅更新基类导入，其余具体算子只修改导入路径。
- 静态核对包的懒加载、Outcome 导出和依赖方向，确认桥接仍引用同一注册表；仓内当前实现和示例不再引用被移除的模块路径。
- `ruff check sigma2`、`ruff format --check sigma2` 和 `git diff --cached --check` 通过。
- 按用户此前要求，未编写或运行测试，也未运行示例；本次运行时行为未验证。现有测试仍使用旧接口，部分测试还引用本次移除的旧路径。
