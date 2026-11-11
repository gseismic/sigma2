# 移除算子类中冗余的配置只读属性

- 创建时间：2026-11-12 02:35 CST
- 创建模型：Codex，环境标示基于 GPT-6；完整模型 ID 未提供，文件名使用 `model-unknown`。
- 分析范围：`WORKTREE`，基准提交 `b6b73b76e727de7e54d025f103057330c41e9c1a`。工作区已有未提交和未跟踪内容，本计划基于当前工作区分析，不代表基准提交包含这些内容。
- 相关工作区：`sigma2/`、`examples/`、`tests/`、`README.md`、`skills/sigma2-usage/` 和 `docs/`；另有任务前已修改的 `AGENTS.md`、`pyproject.toml` 及本地链接。执行时须保留这些已有改动。
- 更新时间：2026-11-12 02:54 CST。更新模型：Codex，环境标示基于 GPT-6；完整模型 ID 未提供。用户要求以本计划为参考并指出问题，以下据当前代码复核并补充执行期验证。

## 目标

按 `docs/HANDOFF.md` 的极简接口原则，检查 `sigma2/` 下全部生产类，移除仅用于读取构造参数或内部指标配置的冗余公开只读属性。保留信号计算、构造参数、必要内部状态、名称与核心算子契约。

## 范围

纳入 `sigma2/` 下全部当前生产类，包括基类、适配器、具体算子和内部辅助类；同时搜索示例、测试及当前文档中的属性调用。排除 `docs/backup/` 中的历史代码，不把测试和示例中的类当作生产 API 删除对象。

计划移除的只读配置属性：

- K 线指标：`rKlineMA` 的 `field`、`n`、`ma_type`；`rKlineRSI` 的 `field`、`n`；`rKlineATR` 的 `n`、`ma_type`；`rKlineBoll` 的 `field`、`n`、`F`；`rKlineMACD` 的 `field`、`fast`、`slow`、`signal`；`rKlineMACross` 的 `field`、`fast`、`slow`、`ma_type`、`stride`；`rKlineKDJ` 的 `n1`、`n2`、`n3`、`ktimes`、`dtimes`；`rKlineMFI` 的 `n`；`rKlineVWAP` 的 `n`、`ma_type`。
- 收益和 Outcome：`rKlineReturn.lag`；`rKlineFutureChange.field`；`rKlineFutureReturn.field`、`return_type`；`rKlineFutureHighLowChange.reference_field`；`rKlineATRBoundTrigger.x_unit_ub`、`x_unit_lb`、`atr_n`、`atr_ma_type`。
- 适配器和截面算子：`rPyta2Signal.fields`、`history_window`；`rKlineBundleReturnRank.lag`、`ascending`；`rKlineBundleFixedWeightIndex.field`、`weights`；`rKlineBundleMarketCapWeightedIndex.field`。

保留 `rOperator` 的状态、输入输出和缓存属性（如 `schema`、`output_keys`、索引、时间窗口、`outputs`、`meta_info`），以及具体算子的 `full_name`。它们承载当前核心调用、输出身份或元数据契约，不属于单纯的构造参数读回属性。保留 `name`、`family` 等类级身份与输入描述。构造参数和计算所需的私有字段、指标对象、缓存窗口均保留。

## 接口取舍

常见场景包括按默认或指定字段构造指标并逐条计算、查询名称、获取输出及时间索引、计算未来收益或边界、按配置生成多标的排名或指数，以及将 pyta2 指标绑定到单个或多个字段。这些场景需要构造参数和运行时状态，不依赖从实例反查构造配置；确需反查的调用者可自行保留传入参数。

方案一保留配置只读属性，能兼容现有反查但增加公开接口；方案二直接移除，保留计算所需的内部配置，符合本次极简要求；方案三先保留弃用转发，能暂时兼容但继续保留冗余接口。选择方案二：不添加兼容层，外部读取被移除属性的代码需调整；构造参数、计算、输出和 `full_name` 保持不变。`rPyta2Signal` 的 `history_window` 仅初始化 deque 时使用，验证后作为局部变量，不额外保留同值实例字段。

## 当前依据与约束

- `docs/HANDOFF.md` 记录 `rKlineMA.field`、`n`、`ma_type` 尚未移除，并建议在无需从实例结构化反查配置时删除；同一文档也明确此前 `used_fields` 的授权不能外推。本次范围以用户当前要求覆盖全部生产类的属性盘点。
- 当前代码中，候选 getter 目前没有被其他生产类依赖；类自身会在计算或 `full_name` 中读取配置 getter，`rPyta2Signal.fields` 和 `history_window` 也用于输入绑定和窗口初始化。移除 getter 时须把内部读取改为私有字段或内部指标对象，不能删除实际计算状态。
- 当前仓内 `examples/006_kline_pyta2.py` 读取 `signal.fields`，`examples/008_kline_missing.py` 读取 `ma.field`。候选 getter 的外部仓库使用情况未知；移除会改变这些实例的公开接口，不添加兼容转发属性。
- 测试中有 `rPyta2Signal.fields` 断言；另有旧版 K 线测试对当前 `rKlineMA`、`rKlineATR` 读取 `history_window`，而当前实现并未提供这些属性。`docs/TODOS.md` 已记录历史测试套件整理事项 `TD-20261112-0209-001`；本任务不扩展为整体测试套件迁移或清理。
- 工作区已有大量改动。本计划不授权覆盖或回滚既有改动，也不授权修改 `GOAL.md`。

## 实施步骤

1. 实施前复核候选清单和当前差异，确认所有属性所在类、仓内引用及所属文件；如发现属性承担核心契约或超出上述范围，先更新计划再改代码。
2. 删除清单中的公开只读 getter。对类内部读取改为使用现有私有配置或子指标对象，保留计算窗口、字段选择、输出 schema 和 `full_name` 字符串。
3. 更新示例及当前有效文档中的候选属性调用。对历史测试先区分是否属于当前支持的契约，不顺带重构 `TD-20261112-0209-001` 涉及的整体测试套件。
4. 全仓搜索已删除的实例属性访问，复核所有生产类声明和差异，确保没有因替换访问路径而改变计算逻辑或名称格式。

## 验证方式与完成标准

- 搜索生产代码、示例、当前文档和适用测试，确认不存在对已移除 getter 的直接访问；构造参数名称仍可用于创建对应算子。
- 逐类检查差异，确认内部计算仍使用同一配置值，输出字段和 `full_name` 组成未被改动。
- 执行当前契约测试并增加针对本次公开接口及非默认参数计算的验证；验证字段绑定、时间窗口、收益类型、阈值名称、排名方向和权重。运行全部独立示例及变更文件的 Ruff 检查。历史全量测试收集问题已记录于 `TD-20261112-0209-001`，不能据此宣称全量测试通过。
- 完成标准：清单中冗余 getter 均已删除；实例计算、输出契约和身份名称实现未被无关改动；示例与当前文档不再调用被删除属性；差异不混入本任务范围外的改动。

## 主要风险与回滚

- 删除公开属性会使仓外读取这些属性的代码报错，仓外调用情况未知。用户明确要求移除，本计划不保留兼容 shim；实施结果中应列明被移除的属性。
- 若内部代码仍通过已删除 getter 读取配置，会造成运行时错误。通过逐类代码检查和全仓引用搜索发现并修正。
- 若名称格式使用被移除 getter 拼接，可能造成输出身份变化。改为读取等价的私有配置或子指标字段，并对照原有格式复核。
- 回滚时只恢复本计划移除的 getter 和相应访问路径，不回滚或覆盖已有工作区改动。

## 实施前自查

- **设计检查**：删除范围限定在配置读回 getter；核心算子属性、身份和计算状态明确保留。
- **遗漏检查**：候选清单覆盖当前 `sigma2/` 中搜索到的所有公开 `@property`，并把示例、测试和文档作为调用方一并检查。
- **约束检查**：不修改 `GOAL.md`，不处理未授权的整体旧测试套件迁移，不覆盖工作区已有改动。
- **执行复核（2026-11-12 02:54 CST）**：原计划只要求静态搜索，缺少执行阶段明确的行为测试，已补充；适配器窗口大小无需长期另存，已调整。变更前当前契约测试 17 项通过，旧 `tests/test_pyta2_adapter.py` 因引用已不存在的 `sigma2.kline.pyta2` 无法收集，属于已有测试整理事项。
