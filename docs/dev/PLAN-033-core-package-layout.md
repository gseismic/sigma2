# PLAN-033：按数据类型整理 core 目录

创建时间：2026-10-29 14:38 CST
状态：已完成。

## 背景

`sigma2/core` 当前混有通用算子、K 线、截面、订单簿、成交和 pyta2 适配实现。各个数据 family 已有自己的包，但实际实现及 family 基类仍集中在 core。用户要求将 `core/kline.py` 的实现归入 `sigma2/kline`，并对其他 family 做类似整理；`core/signal.py` 中每个类拆为独立文件。

设计依据：`docs/design/core-package-layout-20261029-overview.md`。

## 目标

1. 将 `rOperator`、`rSignal`、`rOutcome` 和因子名辅助拆分到通用 core 单类/单职责模块。
2. 将 K 线、Bundle、订单簿和成交实现归入各自数据类型目录。
3. 将 K 线/Bundle 的私有输入、字段和输出表工具归入所属包的 `_internal`。
4. 将 pyta2 K 线 Signal 移到 `sigma2.kline`。
5. 删除旧的 family-specific core 聚合和子模块；不保留兼容转发。
6. 将跨 family replay API 移至顶层 `sigma2.batch`，更新包导出、仓内导入及测试导入。
7. 逐文件人工 review，更新设计/计划结果和索引，只提交本次文件，按仓库要求提交后立即 push。

## 实施步骤

1. 在 `docs/design` 固定目录边界、导入方向和三轮检查结论。
2. 拆分通用 core 基类与因子名辅助。
3. 迁移单 K 线和 Bundle 实现、工具及对应输出缓存。
4. 迁移订单簿/成交 family 和 K 线 pyta2 adapter。
5. 删除 family-specific core 模块，精简 `core.__init__` 为通用生命周期导出。
6. 将 replay API 放到 `sigma2.batch`，搜索所有仓内 `sigma2.core` 引用并更新到规范路径；人工审阅代码、导入图和完整 diff。
7. 写结果文档，按分钟追加 `docs/dev/INDEX.md`，提交指定文件并立即 push。

## 实施结果

完成时间：2026-10-29 14:55 CST。

结果记录：`docs/dev/PLAN-033-core-package-layout-OUTCOME.md`。

包版本从 `0.10.0` 升至 `0.11.0`，反映旧 family-specific core 和 batch 导入路径的有意移除。

## 非目标

- 不改变任何算法或输入输出协议。
- 不更名公共类或改变 `full_name`、schema、因子身份及数值。
- 不保留旧 family-specific core 导入路径；调用方迁移至规范包。
- 不新增或运行测试、lint 或编译检查；按当前执行指令进行源码和 diff 人工审阅。
- 不包含工作区中已有未跟踪的 `docs/design/pyta2-composition-20260924-problem.md`、`docs/ref/crypto.factor_make` 和 `pyta2` 链接。

## 验收

- 每个 family 实现位于对应数据类型目录，通用 core 模块职责明确。
- `core/signal.py` 只定义 `rSignal`，`rOperator` 与 `rOutcome` 各有独立文件。
- `sigma2.core` 只包含通用生命周期和身份工具，batch 位于 `sigma2.batch`。
- 仓内 family 实现、示例和测试不再从 `sigma2.core` 导入 family-specific 对象。
- 人工审阅确认没有重复算法实现、导入环或非本次工作区文件混入提交。
