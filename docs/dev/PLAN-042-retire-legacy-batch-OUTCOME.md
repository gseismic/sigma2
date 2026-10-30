# PLAN-042：实施结果

- 完成时间：2026-10-30 06:35 CST
- 计划：`docs/dev/PLAN-042-retire-legacy-batch.md`
- 设计：`docs/design/retire-legacy-batch-20261030-overview.md`

## 结果

- 归档旧 `sigma2/batch.py` 和未适配当前 core 的整个 `sigma2/kline_bundle/`，同时移除对应的顶层导出；现行批量入口为 `forward_step_apply`。
- 归档仅供旧实现使用的 K 线内部输入及数据辅助、`KlineBar` 和未被生产代码调用的 `qualify_factor_name`；清理相关导出。
- 更新 README、当前设计说明、备份说明和使用指南；明确未来 Bundle 需要另行设计。
- 原 `tests/` 未修改，其中部分测试仍引用已归档的接口，后续需按新契约处理。

后续 PLAN-043 已按新契约重建 Bundle Signal 和价格排名，旧实现继续保留在备份中。

## 审阅与检查

- 对照原 Git 版本逐文件比较，本次归档源码内容一致；静态搜索确认现行源码和示例没有对归档接口的引用，core 没有引入具体市场数据模块。
- `ruff check sigma2 examples`、`ruff format --check sigma2 examples` 和 `git diff --check` 通过。按用户要求，未编写或运行测试，也未运行示例。
- 本轮改动未提交，保留在工作区供审阅。
