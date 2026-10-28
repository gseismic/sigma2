# PLAN-027：横截面 KlineBundle 与 Operator 生命周期

创建时间：2026-10-28 07:36 CST
状态：实现与验证完成；提交状态见 git。设计依据：[Operator、Signal 与 Outcome](../design/sigma2-operator-signal-outcome-20261028-overview.md)、[KlineBundle 横截面](../design/kline-bundle-20261028-overview.md)。

## 目标与范围

实施所选方案 A：一步接收一份多 symbol 时点快照，一个算子可输出各 symbol 结果和计算横截面排名。同时迁移已讨论的 `rOperator / rSignal / rOutcome` 生命周期、pyta2 schema、结果索引、现有 K 线 Signal 与未来计算、batch 和公开文档。此变更不兼容旧版 K 线展开参数和旧窗口元信息，版本提升至 0.7.0。

## 工作步骤

1. 修订设计稿，只保留时点快照，明确 symbol 轴、schema、缺失、缓存、未来期和恢复契约。
2. 按输入数据类型分包：`sigma2/kline/` 与 `sigma2/kline_bundle/` 并列，各自放置 `KlineBar`、`KlineBundle` 数据模型；校验身份、时区、时间、成员及可用时间，提供字段数组与缺失标记。领域包按需导出因子，避免数据类型和 core 的循环导入。
3. 新增 `rOperator` 和 `rOutcome`，将 `rSignal` 收敛为零未来期；统一 `n_backward`、`n_forward`、`min_periods`、`result_index`、pyta2 `Schema`、输出转换和缓存配置，保留故障锁定。
4. 为单 K 线和多 symbol 快照分别定义 family；Bundle family 使用固定 symbol 轴、逐 symbol 输出表、历史窗口与独立状态。按 pyta2 标量 Space 描述每个 symbol，并用 pyta2 表工具存储 symbol 元素；支持关闭、调整及无限输出缓存。
5. 迁移现有单 K 线指标、均线组合及 pyta2 桥接；提供 Bundle 映射算子，为每个 symbol 复用独立单 K 线算子，并为缺失输入生成显式占位。对当前 pyta2 新基类未兼容的 ATR/KDJ 使用明确定义的有界状态实现。迁移 orderbook/trade 的核心构造，保持其现有事件输入方式。
6. 将单 K 线未来计算迁入 `sigma2.kline.outcome` 并继承 `rOutcome`，实现未来收益、变动、最高最低变动、ATR 边界触发；Bundle 映射与未来收益入口按共同快照计数并正确处理缺失。
7. 在 `sigma2/kline_bundle/` 新增横截面排名及过去 N 步收益排名，明确有效集合与平局规则；提供公开导出和 batch 封装。
8. 修改 batch replay，支持 Bundle 输入、多 symbol 输出、Outcome 回填及元信息；其他 family 保留列式输入。更新 README、示例和扩展指南。
9. 根据用户确认迁移并运行测试，覆盖单 K 线和 Bundle 输入、缺失、缓存、结果对齐、pyta2 共同契约及其他 family；静态审查全部修改，发现问题先修复再重审。
10. 生成本计划对应的 OUTCOME，在 `docs/dev/INDEX.md` 追加计划与结果摘要；仅暂存本次文件，中文详细 commit，并立即 push。

## 完成条件

- 设计中只保留 Bundle 时点快照；核心设计中的接口、时间索引及 schema 已同步。
- 单 K 线与 Bundle 的领域代码按数据分包；Bundle Signal/Outcome 接收快照并一次输出所有 symbol，排名、未来收益、空缺、固定集合和重新运行的契约完整。
- 批量结果按共同位置回填，时间和 symbol 元信息可获得；schema、缓存默认值及无状态/有状态错误行为符合设计。
- 现有公开因子、其他 family、文档及示例已迁移，不静默依赖未迁移的 pyta2 旧接口；依赖版本限制明确。
- 完成代码审查、结果和索引记录，提交并推送；保留用户已有的未跟踪文件。

pyta2 当前迁移前后均报版本 `0.0.1`，无法用版本下界区分接口。实施期间上游从 `cb6e8643b6200ecf7a807cc594b78274d05ce96e` 更新到已推送的 `85a2e84969a4a6aa9e201e9f57dc639e4b026827`，将位置属性同步改名为 `result_index`。本计划固定依赖到后者，并用该提交复核和运行测试；未来可在 pyta2 发布可区分版本后改回版本范围。

运行真实场景示例时发现该 pyta2 提交在包初始化时导入 `scipy.stats`，但自身依赖声明没有包含 scipy；本次在 sigma2 依赖中显式声明 scipy，避免干净环境导入失败。这个上游依赖缺失应在 pyta2 后续独立修复。

批量元信息记录结果产生的行情时点和输入数据最早齐备的时间；离线重放无法知道实时计算及发布延迟，不将输入齐备时间冒充结果实际可用时间。

代码审查发现当前 pyta2 KAMA 将缺失窗口写入递推状态后可能长期保持 NaN；sigma2 在调用该指标时对无效窗口重置子状态，并等待有效窗口后恢复。其他指标保留各自的缺失处理契约。

对照 pyta2 源码后，未来收益和变动要求锚点及全部未来区间对应字段有效；未来变动的 schema 字段沿用 `value`。盘口和成交的列式 batch 保留一维列校验并按位置读取，避免带非默认索引的表格发生错位。

迁移测试发现两级均线 V2 的 KAMA 身份遗漏 `stride`，且直接调用 `forward()` 会推进内部指标。恢复完整身份和生命周期保护，避免结果列重名与子状态意外推进。
