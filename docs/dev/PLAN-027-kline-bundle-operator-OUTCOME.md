# PLAN-027：KlineBundle 与 Operator 实施结果

完成时间：2026-10-28 08:02 CST
计划：[PLAN-027-kline-bundle-operator.md](PLAN-027-kline-bundle-operator.md)
设计：[Operator、Signal 与 Outcome](../design/sigma2-operator-signal-outcome-20261028-overview.md)、[KlineBundle 横截面](../design/kline-bundle-20261028-overview.md)

## 实施结果

- 增加 `rOperator`、`rOutcome` 及统一的 `result_index`、`n_backward`、`n_forward`、`min_periods`。`rSignal` 的未来期固定为 0；两个分支均采用 pyta2 的 `Schema`、`Space` 和输出转换约定，支持有界、无界或关闭的输出缓存。
- 按输入数据分设 `sigma2.kline` 与 `sigma2.kline_bundle`。`KlineBar` 是单 symbol 的一根 K 线；`KlineBundle` 是固定 symbol 顺序的同一时点快照。Bundle 的字段数组和输出按 symbol 轴对齐，缺失 Bar 不向前填充。
- 增加单 K 线和 Bundle 的 Signal、Outcome、窗口 family，Bundle 到单 K 线算子的映射适配器，以及截面排名、过去 N 步收益排名、均线和未来收益。缺失成员以显式占位推进每个子算子，支持重置重放。
- 将未来计算迁移到 `sigma2.kline.outcome`，批量 Outcome 按 `result_index` 回填锚点。未来收益及变动要求锚点和整个未来区间对应字段有效。`result_input_ready_at` 仅表示此前输入齐备时间，实际计算和发布延迟由上层记录。
- 迁移原有单 K 线因子、pyta2 桥接、盘口和成交核心构造、README、示例及 sigma2 使用指南。当前 pyta2 尚未迁移的 ATR、KDJ 和未来路径计算由 sigma2 以有界状态实现；为内置 KAMA 增加缺失后恢复，并修复两级 KAMA 身份缺少 `stride` 和直接调用钩子造成状态推进的问题。
- 上游 pyta2 在实施期间将 `target_index` 改为 `result_index` 并推送提交 `85a2e84969a4a6aa9e201e9f57dc639e4b026827`。由于新旧接口均标为 `0.0.1`，sigma2 固定该提交，同时显式声明其包初始化所需的 SciPy 依赖。

## 兼容性与边界

版本升至 0.7.0。K 线输入从展开 OHLCV 改为对象，旧的 `sigma2.kline.target` 路径和 `horizon` 参数不提供兼容层；缓存默认改为最近一步。完整迁移说明见 README。

Bundle 的 symbol 集合和顺序在运行段内固定；成员变化须创建新运行段并在需要时重放。未来期表示输入快照数，不自动对应自然日。Bundle 的 Space 描述单 symbol 值；横截面缓存通过 pyta2 标量列保存各 symbol 元素。某些 pyta2 dtype 的缺失哨兵与缓存转换存在限制，见设计稿。

## 审查与验证

1. 复核了设计中的输入 family、结果所属位置和可用时间：单 K 线与多 symbol 截面分别对应独立目录，Outcome 在结果成熟时回填，缺失快照不会造成共同时间轴错位。
2. 复核了 schema、缓存及状态：单 symbol 使用 pyta2 表，Bundle 表保留 symbol 与 Space 形状；输入验证在状态推进前执行，计算或缓存失败后锁定，成功重置后重放。
3. 复核了与上游的差异和部署依赖：比对并固定已推送的 pyta2 具体提交；通用桥接要求调用方提供已验证的历史长度，不能将其用于要求完整前缀的任意指标。

验证环境使用本机 Python 和 pyta2 `85a2e84` 源码：

- `PYTHONPATH=/home/lsl/macbook/pai-studio-fin/library/pyta2 python -m pytest -q`：159 项通过。覆盖原有因子迁移、pyta2 schema/缓存对照、Bundle 排名、缺失、映射、结果对齐、故障与重放等。
- `ruff check sigma2 examples tests` 与 `git diff --check`：通过。
- 9 个编号示例和 README 中 3 个 Python 代码块运行通过。
- 在临时虚拟环境安装项目副本，确认 pip 从远端安装指定的 pyta2 提交，并在该环境运行全部 159 项测试通过。该环境启用 `--system-site-packages`，复用了本机基础依赖。

本次没有在完全隔离的空环境中重新安装所有基础依赖，也没有进行大规模截面性能测试。提交与推送状态以 git 记录为准。
