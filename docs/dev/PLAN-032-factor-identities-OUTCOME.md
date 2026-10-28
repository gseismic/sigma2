# PLAN-032 实施记录

更新时间：2026-10-28 17:49 CST。
状态：已完成；分多个检查点提交。

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

## 检查点四：缺失恢复、文档与应用联调

更新时间：2026-10-28 18:05 CST。

- pyta2 PLAN-042 修复 KAMA 遇到缺失值后无法恢复的问题；固定依赖更新至 `93ab75884e137bc4133b9445bc900a0a8468624c`，核查 KAMA 均线交叉恢复。
- 更新 README 和使用 skill 的作用域、共享公式列与指标入口。sigma2 全部 237 项测试、相关 Ruff、skill 校验和 examples 目录内 10 个示例通过。
- factor_make 在临时 iosql 中验证多标的、预热缺口、分批保列和未来结果；用真实 Binance 行情对两个标的、11 个指标和 ATR 目标进行短区间计算，各写入 22 行到临时库。生产因子库未写入。
- pyta2 尚有本计划以外的旧 Effect/指标未迁移，不能笼统视为均可使用；详情见 pyta2 TODO。
