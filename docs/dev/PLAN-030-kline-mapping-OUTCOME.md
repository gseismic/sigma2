# PLAN-030：字典式 K 线输入与字段映射实施结果

完成时间：2026-10-28 15:24 CST
计划：[PLAN-030-kline-mapping.md](PLAN-030-kline-mapping.md)
设计：[字典协议作为算子输入](../design/step-mapping-20261028-overview.md)

## 实施结果

- 单 K 线 `step(bar)` 支持字典和只读映射；OHLC 四个逻辑字段必需，volume、symbol、时间及其他字段按算子需要提供。自定义算子可通过 `required_fields` 声明其他必需字段；缺键在索引及状态推进前报错。
- 增加 `key_map={逻辑字段: 输入字段}`，默认同名，显式映射直接读取原始字段，不做链式映射。映射配置保存于元信息，并贯通单步、窗口、批量、组合和所有具名批量入口。无关的额外字段不被丢弃。
- Bundle 字典使用 `{"bars": {symbol: bar}}` 表示一个时点；保留固定 symbol 结果轴、缺失标的和独立子算子状态。`key_map` 应用于各 Bar，`bundle_key_map` 应用于顶层；`required_bundle_fields` 声明顶层必需字段。批量字典输入明确提供 symbol 全集，不从稀疏首行推断。
- 单 K 线批量支持逐行字典、列式字典以及 pandas / polars DataFrame。可选的 `bar_time` 和 `available_at` 按指定字段读取；时间缺失或部分缺失时表格使用 `g_index`，不推断数据可用时间。Outcome 仍按 `result_index` 回填。
- 保留原有 `KlineBar`、`KlineBundle` 输入及身份、时间校验；旧 Bundle 缺失标的继续使用 `KlineBar` 占位。新增字典输入按调用顺序推进，由上游保证时序和截面同步。
- 更新 README、使用 skill、示例与相关设计文档；版本升至 0.8.0。`crypto.factor_make` 未修改，后续适配时须保留其现有工作区改动。

## 审查与验证

1. 核对了 OHLC、可选 volume 与扩展字段：默认收盘价信号不要求 volume，不使用的 volume 即使不可转为数字也不影响结果；使用 volume 的算子在推进前检查字段存在。
2. 核对了映射及组合：显式映射优先于同名键且不链式转换，配置不可通过返回的副本更改；Bundle 子算子只应用一次映射，缺失标的、额外字段和父子状态均有测试。
3. 核对了时间与输出：缺少或不能比较可用时间时保持未知；部分行情时间缺失时使用观测序号索引；未来结果按锚点回填，避免将回填位置解释成当时可用。Polars 的因子名与索引列冲突时会报错，避免覆盖数据。

验证环境使用本机 Python 3.12 和本地 pyta2 `85a2e84969a4a6aa9e201e9f57dc639e4b026827`：

- `python3 -m pytest -q`：213 项通过，覆盖所有具名 K 线及 Bundle 批量入口、字段映射、旧对象兼容、截面缺失、时间、schema、未来结果和原有回归。
- `ruff check sigma2 tests examples`、`python3 -m compileall -q sigma2 tests examples` 和 `git diff --check`：通过。
- 10 个编号示例从 `examples` 目录直接运行成功；README 的 4 个 Python 代码块分别运行成功。

## 使用边界

- `factor_names` 保持逻辑公式身份，不自动区分不同的数据源映射；消费端需要结合映射元信息、别名或数据集标识避免同名结果覆盖。
- 未配置映射的旧数据对象仍原样交给自定义 `forward()`；字典或配置映射后的输入使用映射视图。自定义算子若同时支持两种输入，应处理对象属性和映射读取。
- 额外字段不被强制复制；自定义算子保存不可复制或未声明的可变对象时，需要自行维护快照。未进行大规模截面性能测试。

提交与推送状态以 git 记录为准。
