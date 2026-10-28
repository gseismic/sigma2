# PLAN-032 实施记录

更新时间：2026-10-28 17:49 CST。
状态：分步实施中。

## 检查点一：稳定因子身份

- 单 K 线构造时用 symbol 作为默认 scope；截面默认 all，并允许显式 scope。通用 Operator 也可设置 scope。
- full_name、formula_names、factor_names 和 schema 字段分别保留；字典输入缺少 symbol 时不改变实例身份。Bundle 的每个输出名仍对应固定 symbol 轴。
- 为数据入库和训练列名组装提供不解析字符串的 qualify_factor_name。
- 因子身份与截面相关测试 24 项通过，Ruff 通过。常用指标包装、未来结果和三仓库联调继续。

## 检查点二：常用指标适配

更新时间：2026-10-28 17:50 CST。

- 将 KDJ、ATR 替换为 pyta2 指标适配，新增均线交叉、OBV、MFI、滚动 VWAP 的单 K 线和 batch 入口。
- 保留用于递推的有限 K 线历史，并让 pyta2 负责公式和缺失状态；固定 pyta2 到本轮迁移后的提交，版本升至 0.10.0。
- 新增与 pyta2 数值对照，短 ATR 周期和均线类型一并核查。边界 Outcome 与联调仍在实施。

## 检查点三：边界 Outcome 复用

更新时间：2026-10-28 17:50 CST。

- 将 ATR 边界 Outcome 的窗口扫描委托给已迁移的 pyta2 Effect，采用有界输入前缀适配，保持连续 ATR 状态及 result_index 对齐。
- schema 使用 pyta2 的 `trigger_location`；比较包含缺失行情的逐步输出。全部 236 项 sigma2 测试与本次文件 Ruff 通过。factor_make 联调及文档仍在实施。
