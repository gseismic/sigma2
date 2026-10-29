# PLAN-041：实施结果

- 完成时间：2026-10-30 06:27 CST
- 计划：`docs/dev/PLAN-041-data-families-step.md`
- 设计：`docs/design/data-families-step-20261030-overview.md`

## 结果

- 盘口和成交使用固定字段 `step`、core 生命周期及字典输出，声明各实例使用的字段；简单自定义信号可只实现 `forward`。
- 迁移单 K 线价格、动量、交叉、量价、Outcome 和 pyta2 桥接，状态集中在 `_state`；Signal 与 Outcome 共用简短的固定 K 线输入。均线交叉周期命名为 `fast`、`slow`。
- 为 ATR 和 Boll 增加批量入口；其他 Signal 的批量入口统一使用 `forward_step_apply`。通用重放支持 Outcome 按锚点回填，使用 schema 的缺失哨兵；已存在状态时仅返回本次输入范围。
- 旧窗口、指标封装、两级均值代码与失效示例归档到 `docs/backup/v-0.11/`。Bundle 和旧 batch 尚未迁移，仍使用的旧 K 线数据辅助予以保留。
- 按用户给出的分级编号规范重排 13 个独立示例；第一个展示均线，每个示例自带数据，不依赖其他示例文件。更新 README、设计说明和随仓库提供的使用指南。

## 审阅与检查

- 静态对照固定版本 pyta2 的指标、effect、schema 和 `VectorTable`；检查输入窗口、预览快照、输出键、未来结果索引、实例字段声明、导出以及示例引用。core 未引入 K 线、订单簿或成交模块。
- 相关源码和示例的 `ruff check`、`ruff format --check`、`git diff --check` 通过；按用户要求未编写或运行测试，也未运行示例。运行结果、深复制及未结束观测的实际行为仍待后续验证。
- 本轮实施时改动未提交并保留供审阅，用户随后要求提交；先前批量入口改动已按用户要求提交并推送。
