# PLAN-018：K 线因子库与 batch 配对接口

更新时间：2026-09-22 22:36 CST

状态：已完成

设计依据：

- `docs/design/sigma2-20260922-v5.md` v5.1
- `docs/design/kline-factor-20260922-template.md`
- pyta2 当前 rolling / batch / registry 公共实现

## 目标

实现同源的在线与批量 K 线因子 API：`rMA/MA`、`rRSI/RSI`、`rMACD/MACD`、`rBoll/Boll`、`rKDJ/KDJ`、`rATR/ATR`。均值可以选择 `ma_type`、K 线 `field` 和高级 `ma_kwargs`；batch 输出可直接作为回测或机器学习特征列。

## 范围

1. 为 `rSignal` 实现 v5 的 `update_last()`、状态检查点、faulted 防护、pyta2 子指标生命周期 helper 和 `factor_names`。
2. 为 kline/orderbook/trade family 增加同签名 `update_last()`；future effect/target 类显式拒绝该语义。
3. 新增 `forward_signal_apply()`，对列式 family 数据进行 finalized replay，并提供 dict/tuple/list/DataFrame 输出。
4. 新增 K 线 pyta2 component 内部模板。
5. 每个因子独立文件，实现 rolling 类与同名 batch 函数。
6. 保留现有 `rSMA`、`rPyta2Signal`、`rPyta2SMA` 兼容入口。
7. 更新公共导出、README、版本与交接文档。
8. 增加 contract、数值、batch、update-last、full-name 和导入路径测试。

## 非目标

- 不实现 FeatureSpec、DAG、自动 wrapper catalogue 或训练框架。
- 不实现任意历史位置 rollback。
- 不把 future effect/target 混入正向因子 batch API。
- 不为每个 MA 类型新增 sigma2 类。

## 实施步骤

1. 先实现 core 生命周期与 batch runner，运行现有回归测试。
2. 实现 `_rKlineIndicatorFactor` 与 `rMA/MA`，验证全部 pyta2 MA 类型和字段绑定。
3. 分文件实现 RSI、MACD、Boll、KDJ、ATR。
4. 补齐 public exports、文档示例和版本号。
5. 运行全量测试与 compile 检查。
6. review 公共 API、状态恢复、数值一致性和未跟踪文件隔离；发现问题先修复。
7. 生成 `PLAN-018-kline-factor-library-OUTCOME.md`，追加 `docs/dev/INDEX.md`，提交并推送。

## 执行摘要

- core 生命周期、batch runner、内部 factor component 模板均已完成。
- 六组 rolling/batch 因子已按独立文件实现并从 family 与顶层导出。
- README、v5.1 设计落点、交接、版本号和扩展模板已同步。
- 78 项测试、Ruff 和 compileall 均通过；详细结果见对应 OUTCOME。

## 验收标准

- 六个 rolling 类和六个 batch 函数均可从 `sigma2.kline` 与顶层 `sigma2` 导入。
- `rMA` 支持 pyta2 已公开 MA 类型、标准 K 线字段和 `ma_kwargs`。
- 六类因子的 schema/window 来源于对应 pyta2 组件，full name 包含字段 binding。
- 单输出与多输出 `factor_names` 确定且无冲突。
- batch 与逐条 Signal replay 数值相同；结果长度与输入相同。
- `update_last()` 重复调用幂等，且继续 step 后与最终 K 线序列重放相同。
- future effect/target 不会错误继承最后观测修订语义。
- 原有测试全部通过，新测试覆盖上述契约。
- 只提交本计划范围文件，不包含用户的 `AGENTS.md`、`docs/ref/` 或本地软链接。
