# PLAN-031：多 symbol 快照字段实施结果

完成时间：2026-10-28 16:08 CST

## 实施结果

- Bundle 输入统一为 `{"open_time": t, "bundle": {symbol: bar}}`；快照、截面和每根 Bar 都接受 `Mapping`。`open_time` 可省略，`bundle` 和每个 Bar 的 OHLC 为必需字段，其他字段由算子按需声明，额外字段保留。
- `bundle_key_map` 对截面顶层配置逻辑字段到输入字段的映射，`key_map` 作用于各 Bar；配置的实际字段缺失时不回退。`bars` 和 `bar_time` 按普通额外字段处理，不触发自动字段识别。
- 根据用户要求，不增加旧结构兼容分支。移除与字典协议不一致的 `KlineBundle` 数据类、对象专用的时间和周期校验，以及批量和组合算子中的对象专用分支。单 K 线输入及 `KlineBar` 不在本次调整范围。
- 行情时间进入 `last_bar_time`、`bar_times` 等元信息，批量表格继续使用与单 K 线一致的通用索引名 `bar_time`。不从行情时间推断 `available_at`；缺失 symbol 对应的子算子占位继承截面行情时间。
- 更新 README、示例、sigma2 使用 skill 和设计入口，将已有截面测试改为字典输入；包版本升至 `0.9.0`。本次没有修改 `crypto.factor_make`。

## 审查与验证

按输入与映射、必需和额外字段、时间和状态对齐三轮审查，覆盖字段名冲突、显式映射源缺失、只读 Mapping、symbol 全集、缺失标的和 Outcome 锚点回填。

验证环境为 Python 3.12.8，使用本地 pyta2 提交 `85a2e84969a4a6aa9e201e9f57dc639e4b026827`：

- `python3 -m pytest -q`：228 项通过，包含 pandas 和 polars 结果索引检查。
- 10 个编号示例从 `examples` 目录直接运行成功；README 的 4 个 Python 代码块分别运行成功。
- `ruff check sigma2 tests examples`、改动 Python 文件的 `ruff format --check`、`python3 -m compileall -q sigma2 tests examples` 和 `git diff --check` 通过。

本次未评估大规模截面的性能；时间顺序、周期和截面同步由数据源保证。
