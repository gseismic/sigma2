# PLAN-029：说明 K 线输入适配与预热含义

创建时间：2026-10-28 14:27 CST
状态：实施与验证完成；输入协议与 `PLAN-030-kline-mapping.md` 一起完成，提交状态见 git。

## 目标

根据用户提出的问题，更新 sigma2 的 README 与使用 skill，说明字典输入契约以及 `n_backward`、`n_forward` 和 `min_periods` 的区别，帮助旧接口迁移时正确处理预热。字典协议的具体实施见 PLAN-030。

## 步骤

1. 在 README 中给出 SMA 预热及未来期的含义，解释观测数与日历时间、递推状态之间的区别；同步说明字典和字段映射。
2. 在 `skills/sigma2-usage` 中同步这些契约，避免将旧 `required_window` 直接按原值替换为 `n_backward`。
3. 对照实施后的 sigma2 和 pyta2 时间契约审阅文档，检查链接及文本；消费方代码留待后续适配。
4. 编写结果、追加历史索引，中文提交并推送。
