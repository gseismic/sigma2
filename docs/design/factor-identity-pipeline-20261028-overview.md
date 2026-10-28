# 因子身份、常用指标与入库设计

创建时间：2026-10-28 17:32 CST
状态：已实施；跨项目路径以各仓库实际工作区为准。

## 目标与分层

为量化数据准备提供可追溯的结果名称和常见指标计算。`factor_make` 只使用 sigma2 定义和推进信号，sigma2 绑定 K 线输入、生命周期及 symbol 轴，pyta2 提供指标公式与 rolling 内核；同一指标公式只维护一份。数据和训练目标的使用方式由消费层决定。

本次覆盖均线族 SMA/EMA/WMA/HMA/DEMA/TEMA/KAMA/ZLEMA、RSI、MACD、Boll、KDJ、ATR、均线交叉、收益/跳空及常用量能 OBV/MFI/VWAP。前五项中未完成迁移的 pyta2 实现先依照均线的固定预热契约迁移，再由 sigma2 包装。已有自定义实体比例和两级均线使用 sigma2；未来方向与 ATR 边界目标采用 Outcome 并按 `result_index` 对齐。

ATR 边界扫描也复用 pyta2 Effect，schema 使用 pyta2 的 `trigger_location`。KAMA 核心在无效窗口后重置并重新预热，组合指标沿用同一恢复规则。

## 名称与 schema

| 对象 | 公式名 `full_name` | 结果名 `factor_names` |
| --- | --- | --- |
| 已指定标的的 K 线 | `RSI(14)[close]` | `BTCUSDT:RSI(14)[close]` |
| 多字段的单标的 | `MACD(26,12,9)[close]` | `BTCUSDT:MACD(26,12,9)[close].dif` 等 |
| 截面 | `kline_rank(close,ascending=True)` | `all:kline_rank(close,ascending=True)`；作用域可由用户指定 |
| 未指定标的的单 K 线 | `RSI(14)[close]` | `RSI(14)[close]`；汇总数据时调用方补充标识 |

保留 pyta2 schema：`step(return_dict=True)` 仍使用 schema 输出键。带作用域的 `factor_names` 服务结果列与存储身份。作用域在构造时确定；字典中 `symbol` 仍可选，不通过每个输入动态改名。其他 family 可显式提供作用域。`scope` 与 symbol、具体 symbol 集合和数据源元信息分别保留；截面范围不同时调用方应使用不同作用域。名称字符串供展示和列名使用，不以拆分字符串替代结构化身份。

Bundle 一个结果名对应形状 `(时间, symbol, *space.shape)` 的结果，名称数量仍等于 schema 输出字段数。需要按 symbol 展开宽表时，由消费层结合固定 symbol 轴生成每个列名；截面统计须保留所在全集的身份。

## 预热与持久化

- 单步直接传 `step(bar)`。`n_backward` 是结果前需要的观察数；预热读取按实际历史 K 线条数，而不是简单将根数换算为分钟。递推指标从所选历史起点连续推进，`warmup_multiplier` 只是读取长度策略。
- 未来结果只在 `result_index` 对应的锚点写入；确认时间和有效标志保留，区间末尾缺少未来数据时不能伪造成已成熟。批次切换不重置递推 ATR 状态。
- iosql 物理布局按用户选择采用 `(symbol, open_time)` 行式表，共享公式列；读取或组装训练数据时再组合 `symbol:公式名`。这样避免 symbol 增长导致大量稀疏列，并保持 symbol 作为独立查询维度。带作用域的 sigma2 结果名与物理列通过结构化信息对应，不靠拆分字符串；写入须可重复、保留其他指标、检测同名冲突。
- 原有 `crypto.factor_make` 工作区存在未提交修改和远端之外的提交；在现有内容上修改并保留，不将其余更改混入未经授权的提交或推送。验证使用临时 iosql 库和只读行情数据。

## 三轮设计检查

1. **命名与扩展**：每个计算公式、schema 字段和作用域单独表示；未知 symbol 不生成虚假的标识；`factor_names` 数量不随 symbol 轴增长；允许显式指定截面作用域。
2. **数值与时间**：复用 pyta2 公式；窗口不足、缺失和递推重置规则显式验证；MA 组合的预热不重复累加；未来结果始终回填历史锚点。
3. **数据与依赖**：因子层不直接导入 pyta2；已有未提交的路径规范化与 ATR 跨批连续状态必须保留；写入幂等、列合并、缺失值和 symbol 边界需真实 iosql 往返验证。
