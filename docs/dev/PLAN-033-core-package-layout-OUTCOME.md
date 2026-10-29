# PLAN-033 结果：按数据类型整理 core 目录

完成时间：2026-10-29 14:55 CST

## 完成内容

- `sigma2/core` 仅保留通用算子生命周期 `rOperator`、`rSignal`、`rOutcome` 和因子名工具 `qualify_factor_name`；三个类分别位于独立模块。
- 将单 K 线输入、窗口、pyta2 adapter 和字段工具迁至 `sigma2/kline`。
- 将 Bundle 输入、窗口和 symbol 输出表迁至 `sigma2/kline_bundle`。
- 将订单簿与成交 family 基类分别迁至 `sigma2/orderbook`、`sigma2/trade`。
- 将跨 family replay API 从 `sigma2.core.batch` 移至 `sigma2.batch`。
- 删除旧的 family-specific core 模块及私有工具模块，不保留兼容转发；仓内实现、根包导出和测试导入已改用新路径。
- 将包版本从 `0.10.0` 升至 `0.11.0`。

## 人工审阅

- 检查 `sigma2/core` 的文件边界，确认 `core/signal.py` 只定义 `rSignal`，`rOperator` 与 `rOutcome` 各自独立。
- 搜索 `sigma2` 与 `tests` 下 Python 文件中的旧 family-specific core 模块引用；未发现残留调用方。
- 审阅 family 实现、包导出和 batch 的导入方向，确认 core 不导入数据 family 或 batch。
- 对照迁移前后的实现，`rOperator`、`rSignal`、`rOutcome`、K 线/Bundle 输入与窗口、pyta2 adapter、订单簿/成交基类的方法体、校验条件和计算逻辑均保留；代码改动集中在拆分/移动、导入路径、包导出和移除旧 core 聚合路径。
- 检查本次变更范围，原有未跟踪的 `docs/design/pyta2-composition-20260924-problem.md`、`docs/ref/crypto.factor_make` 与 `pyta2` 链接不属于本次变更。

## 验证范围

未运行测试、lint 或编译检查；本次按执行要求只进行源码、导入引用和 diff 的人工审阅。后续可运行完整测试集验证运行时导入与行为。
