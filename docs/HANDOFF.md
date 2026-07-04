# sigma2 交接文档

更新时间：2026-07-04 10:38 CST

## 项目背景

sigma2 是计划中的金融时间序列 feature 编排库。它应基于 pyta2 rolling 指标内核，提供路径绑定、feature DAG、共享 buffer、rolling/batch 一致执行和 ML 训练矩阵输出能力。

当前项目仍处于初始化规划阶段，尚未实现 Python 包代码。

## 当前仓库状态

- 当前仓库目录：`/Users/mac/pai-studio-fin/library/sigma2`
- 当前分支：`main`
- 已跟踪文件原本只有 `.gitignore` 和 `AGENTS.md`。
- `pyta2` 是指向 `../pyta2` 的软链接，当前为未跟踪状态，只作为本次规划参考。
- 本次新增文档均位于仓库自身目录，不依赖提交 `pyta2` 软链接。

## 本次完成工作

- 阅读 `pyta2/docs/design/pyta2-sigma-20260627-v3.md`。
- 抽查 pyta2 实现，确认 `rIndicator` 已提供 `output_keys`、`schema`、`required_window`、`meta_info`。
- 确认 `rATR`、`rMACD`、`rSMA` 的真实输入签名、输出和窗口形态。
- 创建 `README.md`。
- 创建 `docs/design/sigma2-20260704-roadmap.md`。
- 创建 `docs/dev/PLAN-001-sigma2-roadmap.md`。
- 创建 `docs/dev/PLAN-001-sigma2-roadmap-OUTCOME.md`。
- 创建 `docs/dev/INDEX.md`。

## 核心结论

- pyta2 指标实例是指标元信息事实来源。
- sigma2 不维护完整 `IndicatorDef` registry。
- sigma2 公共 API 应采用双层设计：稳定底层 `FeatureSpec` 加用户友好 DSL。
- `Pyta2Adapter` 必须很薄，只负责实例化、元信息读取、输入校验和 rolling 调用。
- batch 默认必须 replay rolling engine，不能先拼接 pyta2 batch 函数。
- pyta2 当前不允许 `buffer_size=0`，sigma2 adapter 初期应使用 `buffer_size=1`。

## 重要文档

- `README.md`
- `docs/design/sigma2-20260704-roadmap.md`
- `docs/dev/PLAN-001-sigma2-roadmap.md`
- `docs/dev/INDEX.md`
- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`

## 建议下一步

优先实施 `docs/dev/PLAN-001-sigma2-roadmap.md` 的阶段 1 到阶段 3：

1. 创建 Python 包骨架和测试框架。
2. 实现 `FeatureSpec` 与输出命名。
3. 实现 `Pyta2Adapter`，用 rSMA、rATR、rMACD 做最小真实指标测试。

不要先做大量 DSL，也不要先做 batch 性能优化。
