# PLAN-032 实施记录

更新时间：2026-10-28 17:49 CST。
状态：分步实施中。

## 检查点一：稳定因子身份

- 单 K 线构造时用 symbol 作为默认 scope；截面默认 all，并允许显式 scope。通用 Operator 也可设置 scope。
- full_name、formula_names、factor_names 和 schema 字段分别保留；字典输入缺少 symbol 时不改变实例身份。Bundle 的每个输出名仍对应固定 symbol 轴。
- 为数据入库和训练列名组装提供不解析字符串的 qualify_factor_name。
- 因子身份与截面相关测试 24 项通过，Ruff 通过。常用指标包装、未来结果和三仓库联调继续。
