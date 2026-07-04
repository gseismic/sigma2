# PLAN-001：sigma2 初始化规划

更新时间：2026-07-04 10:38 CST

## 背景

当前 sigma2 仓库尚未实现库代码，已有历史仅包含初始化提交和 `AGENTS.md`。用户要求依据 `pyta2/docs/design/pyta2-sigma-20260627-v3.md` 规划本库。

v3 设计的核心结论是：pyta2 指标实例是指标元信息事实来源，sigma2 不再维护完整 `IndicatorDef`，而是围绕 `FeatureSpec`、`FeatureGraph`、`FeatureEngine` 和 `Pyta2Adapter` 做 feature 编排。

## 本计划目标

- 明确 sigma2 的项目定位、边界和目标 API。
- 沉淀后续实现阶段和验收标准。
- 补齐缺失的项目文档体系，便于后续 agent 接续实施。

## 本计划范围

包含：

- 创建 README。
- 创建设计文档。
- 创建计划执行索引。
- 创建交接文档。
- 规划后续实现阶段。

不包含：

- 实现 Python 包代码。
- 引入依赖或发布配置。
- 提交 `pyta2` 软链接内容。

## 后续实施路线

### 阶段 1：项目骨架

任务：

- 创建 `pyproject.toml`。
- 创建 `sigma2/` 包和 `tests/`。
- 建立最小导入测试。
- 明确 pyta2 依赖来源。

验收：

- `python -m pytest` 可运行。
- `from sigma2 import FeatureSpec` 的导入路径有明确目标。

### 阶段 2：FeatureSpec 与输出命名

任务：

- 实现 `FeatureSpec` dataclass。
- 实现 spec 基础校验。
- 实现单输出、多输出和显式 outputs 的列名推导。

验收：

- 单输出默认列名等于 feature name。
- 多输出默认列名为 `{feature_name}_{output_key}`。
- 错误 outputs 配置能稳定抛出 typed error。

### 阶段 3：Pyta2Adapter

任务：

- 用 `return_dict=True` 和 `buffer_size=1` 实例化 pyta2 rolling 指标。
- 读取 `output_keys`、`schema`、`required_window` 和 `meta_info`。
- 通过 `inspect.signature()` 校验 `bind`。
- 把路径 buffer 转换为 `rolling(**kwargs)` 输入。

验收：

- rSMA、rATR、rMACD 均有 adapter 测试。
- 缺少输入绑定和未知输入绑定在初始化时报错。

### 阶段 4：FeatureGraph 与路径系统

任务：

- 实现外部路径和内部 feature 路径解析。
- 支持单输出短路径别名。
- 构建 DAG、拓扑排序、环检测。
- 推导 `effective_required_window`。

验收：

- `MACD -> SMA(macd.dif)` 组合 feature 可正确排序。
- 未知内部依赖、循环依赖、重复输出路径均可稳定报错。

### 阶段 5：rolling engine

任务：

- 实现共享路径 buffer。
- 实现 `FeatureEngine.update()` 和 `FeatureEngine.latest()`。
- 按拓扑顺序执行 feature 节点。
- 组装最新输出行。

验收：

- 同一 `kline.close` 被多个 feature 共享 buffer。
- SMA、ATR、MACD 和一个组合 feature 可滚动计算。

### 阶段 6：batch replay

任务：

- 实现 `FeatureEngine.batch()`。
- batch 内部复用 `update()`。
- 保持输出与输入时间轴对齐。

验收：

- `batch(history)` 与逐行 `update()` 的结果一致。
- 默认不裁剪 warmup。

### 阶段 7：用户 DSL

任务：

- 实现 `SMA()`、`ATR()`、`MACD()` DSL。
- DSL 展开为 `FeatureSpec`。
- 补充 README 端到端示例。

验收：

- 常见 feature 生成可以用短 DSL 完成。
- DSL 展开结果有测试覆盖。

## 风险

- pyta2 作为相邻仓库软链接存在，后续需要决定安装方式或开发依赖方式。
- pyta2 当前没有显式 `input_keys`，sigma2 初期需要使用 `inspect.signature()`。
- pyta2 当前不支持关闭输出缓存，sigma2 初期应使用 `buffer_size=1`。
- batch 性能优化不能早于 rolling 语义稳定。

## 当前建议的下一步

先实施阶段 1 到阶段 3，目标是让 sigma2 能用真实 pyta2 指标完成 spec 校验和 adapter 级 rolling 调用。不要先扩展大量 DSL，也不要先做 batch 性能优化。
