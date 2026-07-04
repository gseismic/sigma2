# sigma2

sigma2 是面向金融时间序列和机器学习特征工程的 feature 编排层。它建立在 `pyta2` rolling 指标内核之上，负责把行情数据路径绑定到指标输入、组织 feature DAG、统一 rolling 与 batch 执行语义，并输出稳定的训练矩阵列。

## 项目定位

- `pyta2` 是指标内核和指标元信息事实来源。
- `sigma2` 不重复维护指标 schema、输出字段和真实窗口。
- `sigma2` 负责数据路径绑定、组合 feature、buffer 共享、执行编排和输出列命名。
- `sigma2` 的 batch 默认通过 rolling replay 实现，保证与实时模式一致。
- 样本裁剪、标签生成、训练集切分和策略回测不属于 sigma2 核心范围。

## 核心抽象

- `FeatureSpec`：描述一次真实 feature 计算，包含 pyta2 指标类、真实构造参数、输入路径绑定和输出命名规则。
- `Pyta2Adapter`：薄适配层，实例化 pyta2 指标并读取 `output_keys`、`schema`、`required_window`、`meta_info`。
- `FeatureGraph`：解析外部行情依赖和内部 feature 依赖，做拓扑排序、环检测和 warmup 传播。
- `FeatureEngine`：共享路径 buffer，并用同一套执行逻辑支持 `update()` 和 `batch()`。
- DSL：在稳定底层 `FeatureSpec` 之上提供 `SMA()`、`ATR()`、`MACD()` 等用户友好构造器。

## 设计依据

主要依据本地参考文档：

- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`
- `pyta2/pyta2/base/indicator.py`
- `pyta2/pyta2/stats/atr/atr.py`
- `pyta2/pyta2/momentum/macd/macd.py`
- `pyta2/pyta2/trend/ma/sma.py`

当前仓库中的 `pyta2` 是指向相邻仓库的软链接，只作为设计与验证参考，不应作为 sigma2 源码提交。

## 当前状态

本库处于初始化规划阶段，尚未实现 Python 包代码。当前高优先级工作是按 `docs/dev/PLAN-001-sigma2-roadmap.md` 先完成最小可验证核心：`FeatureSpec`、`Pyta2Adapter`、路径校验、输出命名和基础 rolling engine。
