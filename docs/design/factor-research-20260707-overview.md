# sigma2 因子分析与研究训练层设计

更新时间：2026-07-07 12:34 CST

## 状态

本文是 `sigma2.research` 因子分析与研究训练层的专题设计文档，便于单独复制、评审和迭代。

它不替代 `docs/design/sigma2-20260704-overview.md`。总设计仍是项目级设计依据；本文是其中研究训练层的独立展开。

核心结论：

- sigma2 core 继续保持轻量，只负责 `rSignal`、family 基类、`step()` 生命周期和信号输出契约。
- 因子分析、IC、RankIC、分组收益、深度学习数据集、强化学习环境和 minbt bridge 都属于研究训练层，不进入 core。
- 研究训练层不应以传统 `FactorAnalysis` 为中心，而应以 `FeatureData -> TargetData -> ResearchDataset -> AnalysisReport / EnvBuilder` 为中心。
- `Factor` 是一种有金融解释意义的 `Feature`；IC 等因子分析能力是 feature 诊断模块，不是整个系统的中心。
- 研究训练层可以先作为 `sigma2.research` 实现，但接口要按未来可拆成独立包 `sigma2-research` 的边界设计。
- 研究训练层只依赖 sigma2 的公共信号协议，不依赖 `sigma2.core` 内部实现。
- 第一阶段重点是形成“从 sigma2 信号生成 feature、生成 target、做 IC/分组收益诊断、导出 ML/DL dataset”的最小闭环。
- RL 环境和 minbt bridge 应在监督学习数据闭环稳定后再做。

## 设计目标

真实目标不是单独做一个因子报告工具，而是支持完整量化研究和训练流程：

```text
market data -> rSignal -> FeatureData -> TargetData -> ResearchDataset -> model / report / env
```

目标场景：

- 传统因子研究：IC、RankIC、IC decay、分组收益、换手、相关性、缺失率。
- 监督学习：从 feature 和 target 构建 tabular dataset。
- 深度学习：构建 sequence、cross-section、cross-section-sequence 张量。
- 强化学习：构建 observation、action、reward、simulator、env。
- 在线推理：复用训练期 feature 顺序、normalizer、mask 和 pipeline 状态。
- 框架桥接：消费 sigma2 signal，也可以桥接 minbt 等回测执行系统。

非目标：

- 不把 IC、因子分析、训练数据集或 RL 环境塞进 `sigma2.core`。
- 不要求所有 feature 都必须来自 sigma2 signal。
- 不让研究训练层调用 `signal.forward()`。
- 不先做复杂 DAG、分布式计算、完整 HTML 报告或自动模型训练平台。
- 不让 minbt 的 `bar/bars` 等外部框架命名污染 sigma2 内部概念。

## 核心概念

### Signal

`Signal` 是 sigma2 core 中的 `rSignal` 或兼容对象，职责是把原始行情流转换成一个或多个信号输出。

关键点：

- 用户通过继承 `rSignal` / family 子类定义信号。
- 用户或 runner 通过 `step()` 推进状态。
- `forward()` 是子类计算 hook，不是研究训练层的入库入口。
- 一个 signal 实例默认绑定一条输入流；多 symbol、多 venue、多数据源由 runner 创建独立实例或 clone。

### Feature

`Feature` 是模型输入。它可以来自：

- sigma2 signal。
- 外部 DataFrame。
- 基本面数据。
- 订单簿派生特征。
- 新闻、事件、embedding。
- 手工特征或模型中间表示。

研究训练层的中心是 feature，不是 factor。

### Factor

`Factor` 是具有金融解释意义、通常用于横截面研究的一类 feature。

典型 factor 诊断：

- IC。
- RankIC。
- IC decay。
- 分组收益。
- 多空组合收益。
- 分位数组合换手。
- 因子相关性和冗余。

因此 factor analysis 是 feature analysis 的子集。

### Target

`Target` 是监督学习标签，例如未来收益、未来中间价收益、涨跌分类、未来波动率或风险目标。

标签生成是最容易产生未来函数的环节，必须单独建模。

### Dataset

`ResearchDataset` 是传统机器学习和深度学习训练的主对象，负责把 feature、target、mask、split、transform 和 sample weight 组织成可训练数据。

### Env

`Env` 是强化学习训练对象，负责组合 observation、action、reward 和 simulator。

RL 不应直接复用 IC 分析模型。它需要交易状态、持仓、现金、费用、滑点和 episode 语义。

## 系统边界

### sigma2 core

职责：

- 定义 `rSignal`。
- 定义 `rKlineSignal`、`rOrderBookSignal`、`rTradeSignal` 等 family。
- 定义 `step()` 生命周期。
- 定义 schema、output keys、`make_dict_output()` 和短输出缓存。
- 提供可继承、可组合、类似 `pyta2.base.rIndicator` 的轻量信号对象。

不负责：

- IC 分析。
- 标签生成。
- 训练集切分。
- 标准化 fit/transform。
- PyTorch Dataset。
- RL Env。
- minbt 订单、撮合、持仓、资金和回测语义。

### sigma2.research

职责：

- 从 signal 或外部数据生成 `FeatureData`。
- 生成 `TargetData`。
- 做 feature/factor 诊断。
- 生成 `ResearchDataset`。
- 提供 DL/RL 训练前的数据形态。
- 提供 minbt bridge，但不重写 minbt 的交易执行语义。

边界：

- 只依赖 `SignalLike` 协议。
- 不调用 `forward()`。
- 不改变 `rSignal` 契约。
- 可以未来拆成 `sigma2-research` 独立包。

### minbt

职责：

- 回测和交易执行语义。
- 订单。
- 撮合。
- 手续费。
- 滑点。
- 持仓。
- 资金账户。

研究训练层可以把 minbt 作为 simulator 或 bridge 使用，但不能让 minbt 命名进入 sigma2 core。

## 推荐源码结构

```text
sigma2/
  research/
    __init__.py
    feature/
      panel.py
      runner.py
      align.py
      transform.py
      store.py
    target/
      forward_return.py
      classification.py
      risk.py
    analysis/
      ic.py
      quantile.py
      turnover.py
      correlation.py
      leakage.py
      drift.py
      report.py
    dataset/
      supervised.py
      sequence.py
      split.py
      torch.py
    rl/
      observation.py
      action.py
      reward.py
      env.py
      trajectory.py
    bridge/
      sigma2.py
      minbt.py
```

模块职责：

- `feature`：生成、对齐、转换、存储 `FeatureData`。
- `target`：生成监督学习标签和风险目标。
- `analysis`：IC、RankIC、分组收益、换手、相关性、泄漏检查、漂移检查。
- `dataset`：ML/DL 训练数据，split、mask、sample weight、tensor 输出。
- `rl`：observation、action、reward、env、offline trajectory。
- `bridge`：连接 sigma2 signal 和 minbt 等外部框架。

## 最小公共协议

研究训练层不应要求对象必须继承 `rSignal`，只需要最小 `SignalLike` 协议：

```python
class SignalLike:
    family: str
    output_keys: list[str]
    step_input_keys: tuple[str, ...]
    schema: object

    def reset(self) -> None:
        ...

    def step(self, **data):
        ...
```

约束：

- `rSignal` 天然满足该协议。
- 外部 feature generator 可以实现该协议进入研究训练层。
- runner 只能调用 `reset()` 和 `step()`。
- runner 不能调用 `forward()`。
- 多 symbol、多 venue、多输入流必须有独立 signal 状态。

## 用户接口

### 生成 feature

最短路径：

```python
from sigma2.kline import rReturn, rSMA
from sigma2.research import make_features

features = make_features(
    data=klines,
    signals=[
        rSMA(20),
        rReturn(5),
    ],
    time="dt",
    symbol="symbol",
)
```

多数据源路径：

```python
features = make_features(
    data={
        "kline": klines,
        "orderbook": orderbooks,
        "trade": trades,
    },
    signals=[
        rSMA(20),
        rBookSpread(),
        rTradeSignedVolume(),
    ],
    time="dt",
    symbol="symbol",
)
```

设计原则：

- 普通用户只传 `data`、`signals`、`time`、`symbol`。
- 不强制用户理解 `KlineInput`、`OrderBookInput` 等重对象。
- 内部可以通过 normalizer、schema、registry 处理字段映射。
- 新数据类型通过新增 family normalizer 和 runner 进入，不修改已有 family。

### 生成 target

```python
from sigma2.research import ForwardReturn

target = ForwardReturn(
    horizon=5,
    price="close",
    start="next",
    return_type="simple",
)
```

关键语义：

- `horizon`：预测周期。
- `price`：`close`、`open`、`mid`、`vwap` 等价格来源。
- `start`：收益从何时开始算，默认应为 `next`。
- `return_type`：`simple` 或 `log`。
- `align`：target 与 feature 时间戳如何对齐。

默认策略：

- `start="next"`，避免默认未来函数。
- 多 horizon target 生成多个 target column。
- target metadata 必须记录 horizon、start、price、return_type 和 align。

### 做因子诊断

```python
from sigma2.research import IC, QuantileReturn, Turnover, analyze_features

report = analyze_features(
    features=features,
    target=target,
    analyses=[
        IC(method="pearson"),
        IC(method="spearman"),
        QuantileReturn(q=5),
        Turnover(q=5),
    ],
)

ic_summary = report.ic.summary()
```

也可以使用字符串快捷方式：

```python
report = analyze_features(
    features=features,
    target=target,
    analyses=["ic", "rank_ic", "quantile"],
)
```

约束：

- `analyze_features()` 默认不写文件。
- 复杂图表、HTML 报告和持久化必须显式调用。
- 报告对象优先返回结构化表格和 summary。

### 生成监督学习数据集

```python
from sigma2.research import WalkForwardSplit, Winsorize, ZScore, make_dataset

dataset = make_dataset(
    features=features,
    target=target,
    transforms=[
        Winsorize(3.0),
        ZScore(scope="cross_section"),
    ],
    split=WalkForwardSplit(train="3y", valid="6m"),
)

X_train, y_train = dataset.train.to_tabular()
X_valid, y_valid = dataset.valid.to_tabular()
```

也可以从原始数据一步生成：

```python
dataset = make_dataset(
    data=klines,
    signals=[
        rSMA(20),
        rReturn(5),
    ],
    target=ForwardReturn(horizon=5),
    split="walk_forward",
)
```

### 生成深度学习序列数据

```python
seq = dataset.to_sequence(
    lookback=60,
    features=["sma", "return"],
    target="fwd_return_5",
)
```

推荐输出形态：

```text
X:    [sample, lookback, feature]
y:    [sample]
mask: [sample, lookback]
```

横截面序列形态：

```python
panel = dataset.to_cross_section(
    lookback=20,
    universe="tradable",
)
```

推荐输出形态：

```text
X:    [time, symbol, lookback, feature]
y:    [time, symbol]
mask: [time, symbol, lookback]
```

### 构建 RL 环境

RL 在第一阶段不优先实现，但接口边界应提前确定。

```python
from sigma2.research import NetReturn, PortfolioObservation, TargetWeight, make_env

env = make_env(
    dataset=dataset,
    simulator=simulator,
    observation=PortfolioObservation(lookback=60),
    action=TargetWeight(max_abs=1.0),
    reward=NetReturn(cost=True, risk_penalty=0.1),
)
```

关键点：

- `simulator` 是协议，不是硬编码 minbt。
- minbt 可以是 simulator 实现。
- reward 必须明确是否扣费、是否考虑滑点、是否加入风险惩罚。
- action space 必须显式，例如目标权重、离散买卖、订单意图。

## 核心数据对象

### FeatureData

`FeatureData` 是研究训练层的核心对象，表示模型输入。

逻辑结构：

```text
FeatureData
  time: 时间轴
  symbol: 标的轴，可选但推荐
  values: feature values
  columns: feature names
  mask: feature 可用性、可交易性或训练可用性
  meta: family、source、signal full_name、schema、version
```

要求：

- 保留 `[time, symbol]` 结构。
- `mask` 是一等公民。
- feature column 必须可追溯到 `family`、`full_name`、`output_key` 和可选版本。
- 不锁死 pandas 后端，后续可支持 numpy、arrow、polars、torch。

### TargetData

`TargetData` 表示监督学习标签。

逻辑结构：

```text
TargetData
  time
  symbol
  values
  columns
  mask
  meta: horizon、start、price、return_type、align
```

要求：

- 默认避免未来函数。
- 多 horizon 标签必须保留 horizon metadata。
- 标签缺失和不可训练样本通过 mask 表达。

### AnalysisReport

`AnalysisReport` 表示 feature/factor 诊断结果。

逻辑结构：

```text
AnalysisReport
  tables
  summaries
  diagnostics
  optional plot data
  metadata
```

要求：

- 默认无外部副作用。
- 文件导出、HTML 生成、图表渲染显式调用。
- 支持程序化读取，例如 `report.ic.summary()`。

### ResearchDataset

`ResearchDataset` 是训练数据主对象。

逻辑结构：

```text
ResearchDataset
  features: FeatureData
  target: TargetData
  masks
  splits
  transforms
  sample_weight
  groups
  universe
  metadata
```

输出能力：

- `to_tabular()`。
- `to_sequence(lookback=...)`。
- `to_cross_section(lookback=...)`。
- `to_numpy(kind=...)`。
- `to_torch(kind=...)`，可选依赖。
- `analyze(...)`。

## 因子分析模块

### IC

IC 用于衡量 feature 与未来 target 的相关性。

默认：

- `axis="cross_section"`。
- `method="pearson"`。
- 每个时间截面对多个 symbol 计算相关性。
- `min_count` 控制每个截面最少样本数。

示例：

```python
ic = IC(
    method="pearson",
    axis="cross_section",
    min_count=30,
)
```

需要支持：

- Pearson IC。
- Spearman RankIC。
- weighted IC。
- group-neutral IC。
- rolling IC。
- IC decay。
- summary：mean、std、t-stat、IR、positive ratio、p-value。

注意：

- 单 symbol 场景不适合默认横截面 IC，应显式使用 `axis="time_series"`。
- 多日 forward return 有重叠样本，t-stat 后续应支持 Newey-West / HAC。

### QuantileReturn

分组收益用于判断特征是否具备可交易的单调性。

示例：

```python
quantile = QuantileReturn(
    q=5,
    long_short=True,
    group_neutral=False,
)
```

需要支持：

- 按时间截面分位分组。
- 每组未来收益。
- top-bottom spread。
- long-short 累计收益。
- 单调性检查。
- group-neutral quantile。

### Turnover

换手用于评估因子组合交易成本敏感性。

需要支持：

- rank turnover。
- quantile turnover。
- top group turnover。
- long-short turnover。

### Correlation

特征相关性用于评估冗余。

需要支持：

- feature-feature correlation。
- cluster 或相关性矩阵。
- 与已有 feature set 的冗余检查。

### MissingReport

缺失率分析用于检查特征可用性。

需要支持：

- 全局缺失率。
- 按 feature 缺失率。
- 按 symbol 缺失率。
- 按 time 缺失率。
- warmup 缺失。

### LeakageCheck

泄漏检查用于发现常见未来函数问题。

候选检查：

- target start 是否为 `next`。
- transform 是否只在训练集 fit。
- split 是否按时间切分。
- target horizon 是否和 validation 边界重叠。
- feature timestamp 是否晚于 target decision time。

### DriftReport

漂移分析用于评估训练集和验证集分布差异。

需要支持：

- feature distribution drift。
- target distribution drift。
- missing rate drift。
- universe coverage drift。

## Transform 设计

Transform 必须有生命周期：

```python
class Transform:
    def fit(self, data):
        ...

    def transform(self, data):
        ...

    def fit_transform(self, data):
        self.fit(data)
        return self.transform(data)
```

原则：

- 训练集 `fit()`。
- 验证集和测试集只能 `transform()`。
- 不允许默认全样本 fit。
- transform metadata 要可保存、可复用到 online 推理。

第一批 transform：

- `Winsorize`：去极值。
- `ZScore`：标准化。
- `Rank`：转 rank 或 percentile rank。
- `Neutralize`：行业、市值、beta 中性化。
- `FillMissing`：缺失填充。
- `DropInvalid`：显式丢弃无效样本。

推荐接口：

```python
transforms = [
    Winsorize(3.0),
    ZScore(scope="cross_section"),
]
```

## Split 设计

默认 split 必须是时间序列友好的。

第一批 split：

- `WalkForwardSplit`。
- `TimeRangeSplit`。
- `PurgedSplit`。

要求：

- 不默认随机切分。
- validation/test 不得泄漏未来。
- 多 horizon target 要考虑标签重叠。
- deep learning sequence 要考虑 lookback 跨 split 边界。

示例：

```python
split = WalkForwardSplit(
    train="3y",
    valid="6m",
    step="6m",
)
```

## Mask 设计

mask 是一等公民，不能简单靠 drop 行解决。

mask 类型：

- feature missing mask。
- target available mask。
- tradable universe mask。
- suspended mask。
- limit up/down mask。
- liquidity mask。
- warmup mask。

原则：

- 保留 `[time, symbol]` 结构。
- 不可训练和不可交易是不同概念。
- `ResearchDataset` 输出 tensor 时必须同步输出 mask。

## Online 推理

训练和上线必须复用同一套 pipeline。

推荐接口：

```python
pipeline = FeaturePipeline(
    signals=[
        rSMA(20),
        rReturn(5),
    ],
    transforms=[
        Winsorize(3.0),
        ZScore(scope="cross_section"),
    ],
)

dataset = pipeline.fit_transform(
    data=train_klines,
    target=ForwardReturn(5),
)

online = pipeline.to_online()
row = online.step(kline=latest_kline)
```

要求：

- `to_online()` 使用训练期 fit 好的 transform 状态。
- online runner 只能调用 signal `step()`。
- online 输出复用训练时 feature column 顺序。
- online 输出保留 mask 和 metadata。

## 数据 family 扩展

研究训练层延续 sigma2 的原则：输入类型决定 family。

简单用户路径：

```python
make_features(
    data=klines,
    signals=[...],
    time="dt",
    symbol="symbol",
)
```

多源路径：

```python
make_features(
    data={
        "kline": klines,
        "orderbook": orderbooks,
        "trade": trades,
    },
    signals=[...],
)
```

高级扩展路径：

```python
registry.register_family(
    family="funding_rate",
    normalizer=FundingRateNormalizer(),
    runner=FundingRateRunner(),
)
```

原则：

- 新数据类型通过新增 family、normalizer、runner 扩展。
- 不修改已有 `kline`、`orderbook`、`trade` 输入契约。
- 普通用户不需要创建 `KlineInput`。
- 高级用户可以通过 schema/normalizer 控制字段映射。

## RL 设计边界

RL 需要单独对象：

```text
observation = 市场特征 + 当前持仓 + 现金 + 风险状态
action = 目标权重 / 买卖方向 / order intent
reward = pnl - cost - risk_penalty
simulator = 执行、撮合、费用、滑点、持仓
env = observation/action/reward/simulator 的组合
```

第一版不直接做完整 RL。

需要先稳定：

- `FeatureData`。
- `TargetData`。
- `ResearchDataset`。
- `FeaturePipeline`。
- simulator 协议。

再实现：

- `PortfolioObservation`。
- `TargetWeight`。
- `NetReturn`。
- `TrajectoryData`。
- `make_env()`。

## minbt bridge

正确关系：

```text
sigma2 core -> signals
sigma2.research -> features / dataset / analysis / env
minbt -> simulator / backtest / execution semantics
```

推荐位置：

```python
from sigma2.research.bridge.minbt import MinbtSimulator
```

未来独立包：

```python
from sigma2_research.bridge.minbt import MinbtSimulator
```

禁止：

- `rSignal`、family 子类、research 主流程中出现 `update_minbt_bars(...)` 这类外部框架命名。
- 在 sigma2 core 中出现 `Broker`、下单、持仓、资金管理概念。
- 为兼容 minbt 把 sigma2 的 K 线统一叫 `bar`。

## 版本规划

| 版本 | 冻结内容 |
| --- | --- |
| `0.1.x` | sigma2 core signal 契约：`rSignal.step()`、family、schema/output |
| `0.2.x` | pyta2 信号基类、常用 K 线信号、最小 signal runner |
| `0.3.x` | orderbook/trade 真实信号和 contract tests |
| `0.4.x` | `FeatureData`、`ForwardReturn`、`analyze_features()`、IC / RankIC / QuantileReturn |
| `0.5.x` | `ResearchDataset`、walk-forward split、transform fit/transform、tabular/sequence 输出 |
| `0.6.x` | 初步 RL env builder、minbt bridge、offline trajectory |
| `1.0.0` | core、常用内置信号和研究训练层主路径正式稳定 |

## Contract Tests

研究训练层至少需要锁定：

- `make_features()` 只调用 signal `reset()` 和 `step()`，不调用 `forward()`。
- 多 symbol 输入使用独立 signal 状态。
- `FeatureData` 保留 feature columns、time、symbol、mask 和 metadata。
- feature column 可追溯到 family、full_name、output_key。
- `ForwardReturn(start="next")` 默认不产生当前收盘到未来收盘的隐式未来函数。
- target metadata 保留 horizon、start、price、return_type。
- `IC(axis="cross_section")` 默认按同一时间截面计算。
- `min_count` 不足时 IC 返回缺失而不是错误值。
- transform 只能在训练集 fit，验证集和测试集只能 transform。
- `WalkForwardSplit` 不泄漏未来。
- `ResearchDataset.to_sequence()` 的 feature 顺序、lookback 对齐和 mask 输出稳定。
- `AnalysisReport` 默认无文件写入副作用。
- `make_env()` 依赖 simulator 协议，不直接依赖 minbt。

## 第一阶段实施顺序

第一阶段目标是形成“信号 -> feature -> target -> 分析 -> dataset”的最小闭环。

建议顺序：

1. 实现最小 signal runner / `make_features()`，只消费 `SignalLike.reset()` 和 `SignalLike.step()`。
2. 实现 `FeatureData`，先支持 DataFrame 输入输出，但内部契约不要锁死 pandas。
3. 实现 `ForwardReturn` 和 `TargetData`，默认 `start="next"` 并记录 label metadata。
4. 实现 `IC`、`RankIC`、`QuantileReturn` 和 `AnalysisReport`，优先返回结构化表格。
5. 实现 `WalkForwardSplit`、`Winsorize`、`ZScore`。
6. 实现 `ResearchDataset.to_tabular()` 和 `ResearchDataset.to_sequence()`。
7. 再实现 `FeaturePipeline.to_online()`，确保离线训练和在线推理复用同一套 feature 顺序和 transform 状态。
8. 最后再做 RL env builder、minbt bridge、torch adapter 和更复杂报告。

暂不优先做：

- 全面迁移 pyta2 指标。
- 复杂 DAG。
- batch 向量化优化。
- minbt 深度集成。
- 自动模型训练框架。
- 完整 gymnasium 兼容层。
- HTML 报告和图表渲染系统。

## 最终判断

推荐路线：

```text
core-first:
    rSignal.step -> root family package -> concrete signal files

research-layer:
    SignalLike -> FeatureData -> TargetData -> ResearchDataset

factor-analysis:
    FeatureData + TargetData -> IC / RankIC / QuantileReturn / Turnover -> AnalysisReport

deep-learning:
    ResearchDataset -> tabular / sequence / cross-section tensor

reinforcement-learning:
    ResearchDataset + simulator -> observation / action / reward / env
```

不要采用：

```text
FactorAnalysis-first:
    因子报告 -> 反向定义所有 feature 和 dataset

FeatureSet-first:
    应用层集合对象 -> 反向定义 rSignal

minbt-first:
    外部框架数据命名 -> 反向污染 sigma2 family
```

结论：

```text
sigma2 core 保持轻量。
research 层负责研究训练闭环。
factor analysis 是 research 层的诊断模块。
深度学习和强化学习是 research 层更高优先级的长期方向。
```
