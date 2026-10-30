# PLAN-043：实施结果

- 完成时间：2026-10-30 06:45 CST
- 计划：`docs/dev/PLAN-043-kline-bundle-rank.md`
- 设计：`docs/design/kline-bundle-price-rank-20261030-overview.md`

## 结果

- 新建固定输入的 `rKlineBundleSignal`，将 Bundle、时间和缺失信息直接交给 core；自定义信号只需实现 `forward`。
- 实现 `rKlineBundleRank`：默认按 close 升序排名，并列取平均名次；缺失 Bar 和非有限价格输出 NaN，未出现在输入中的 symbol 不推断。`used_fields` 根据所选价格字段传入基类。
- 实现批量入口 `KlineBundleRank`，复用 `forward_step_apply`；每个 `rank` 值是一个 symbol 到排名的字典，存入 object 列。空批量输入返回空字典。
- 更新顶层导出、README、使用指南和历史设计说明，新增自包含示例 `examples/401_bundle_rank.py`。先前归档的旧 Bundle 仍保留在备份中。

## 审阅与检查

- 静态审阅 core 生命周期、无 schema 的 object 缓存、pyta2 `DequeTable` 和 `VectorTable` 的对象列写入，以及排名时的相同值、缺失和 symbol 变化处理；core 没有引入具体数据类型。
- `ruff check sigma2 examples`、`ruff format --check sigma2 examples` 和 `git diff --check` 通过。按用户要求，未编写或运行测试，也未运行示例；实际运行行为仍待后续验证。
- Bundle 每条输入视为已确认，提供相同 `open_time` 会触发 core 重复提交检查；未结束截面更新及固定 symbol 轴不在本轮范围。object 缓存与返回的嵌套字典共享引用。
- 本轮改动未提交，连同此前的旧接口归档改动保留在工作区供审阅。
