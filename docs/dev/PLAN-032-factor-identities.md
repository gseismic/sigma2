# PLAN-032：统一因子身份及常用指标

创建时间：2026-10-28 17:32 CST
状态：实施中。

## 目标

依照 `docs/design/factor-identity-pipeline-20261028-overview.md`，为 Signal / Outcome 提供稳定作用域的 `factor_names`，对单标的、截面和其他 family 一致；公开常用指标并复用完成迁移的 pyta2 内核，支持 factor_make。

## 步骤

1. 明确 `full_name`、schema、`factor_names`、symbol、可配置截面作用域与多 symbol 数组形状；为所有入口和 batch 统一传递并检测映射配置。
2. 复用 pyta2 的 KDJ、ATR、MACross、量能指标和 ATR 边界触发 effect，删除 sigma2 中对应的重复公式；对既有输出、预热、缺失、reset 和 batch 做回归。边界扫描在 pyta2 先迁移 Effect 契约后以有限窗口适配。
3. 与 factor_make 的单步、预热、Outcome 对齐和数据写入联调；同步 README、使用 skill、设计与版本依赖。
4. 多轮检查和用户已授权的回归测试、示例及 lint；生成结果文件并追加索引，仅提交本次修改，提交后立即推送。
