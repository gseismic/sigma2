# sigma2 库规划设计

更新时间：2026-07-04 10:38 CST

> 历史备份：本文是早期规划文档，不作为当前实现依据。当前唯一有效设计见 `docs/design/sigma2-20260704-overview.md`。

## 修订状态

2026-07-04 12:08 CST 根据用户反馈修订：sigma2 不应只是 pyta2 的薄封装。本文中 `FeatureSpec + Pyta2Adapter` 的规划应降级为 pyta2 指标适配和矩阵输出层的实现细节；新的核心公共接口以 `docs/design/sigma2-20260704-signal-core.md` 为准，即通用 `rSignal`、数据类型专属信号、标准 K 线输入输出、组合信号和 `SignalEngine`。

2026-07-04 12:11 CST 补充修订：K 线只是第一种数据类型，不是唯一模型。`rSignal` 不应把输入锁死为 OHLCV；OHLCV 契约属于 `rKlineSignal`。未来 orderbook、trades 等应通过 `rOrderBookSignal`、`rTradeSignal` 或同类 data-kind 子类扩展。

## 依据与现状

本设计依据 `pyta2/docs/design/pyta2-sigma-20260627-v3.md`，并抽查了以下 pyta2 实现：

- `pyta2/pyta2/base/indicator.py`
- `pyta2/pyta2/stats/atr/atr.py`
- `pyta2/pyta2/momentum/macd/macd.py`
- `pyta2/pyta2/trend/ma/sma.py`

关键事实：

- `rIndicator` 已提供 `schema`、`output_keys`、`required_window`、`full_name`、`meta_info` 和 `rolling()`。
- `rATR.forward(highs, lows, closes)` 证明 sigma2 需要显式输入路径绑定。
- `rMACD` 是多输出指标，输出键来自 schema：`dif`、`dea`、`macd`。
- `rMACD` 的真实窗口是 `n1 + n3 - 1`，不能假设所有指标都有统一 `window` 参数。
- `rIndicator` 当前不允许 `buffer_size=0`，sigma2 适配层短期应使用 `buffer_size=1`，避免 pyta2 无限输出缓存。

当前 sigma2 仓库几乎为空，只跟踪 `AGENTS.md` 和 `.gitignore`。`pyta2` 是指向相邻仓库的软链接参考，不应纳入 sigma2 源码。

## 最终目标

sigma2 的最终目标是成为金融 ML signal/feature 生成和实时特征计算的轻量信号库：

- 用一份声明同时支持实时 rolling 与历史 batch。
- 提供类似 `pyta2.base.rIndicator` 的通用 `rSignal` 基类，方便用户自定义信号。
- `rSignal` 只规定生命周期、schema、输出和元信息，不固定具体行情输入字段。
- 对 K 线通过 `rKlineSignal` 做标准化：rolling 输入为 `opens, highs, lows, closes, volumes`，单点更新输入为 `open, high, low, close, volume`。
- 对 orderbook、trades 等未来数据类型，通过各自 data-kind 信号子类定义标准输入契约。
- 支持 kline、orderbook、trades 等外部行情路径。
- 支持基于已有 feature 输出继续计算新 feature。
- 可组合 pyta2 指标和自定义 sigma2 信号。
- 输出稳定、可复现、适合训练矩阵的列名。
- 保留清晰的内部接口，后续可优化 batch 性能而不改变用户 API。

## 非目标

- 不实现技术指标数学内核，这属于 pyta2。
- 不维护完整 `IndicatorDef` registry。
- 不做交易策略、回测撮合、订单执行。
- 不负责训练样本裁剪、标签生成、数据集切分。
- 不在第一阶段做向量化 batch 优化。

## 用户接口方案比较

### 方案 A：只暴露底层 FeatureSpec

示例：

```python
FeatureSpec(
    name="sma10_close",
    cls=rSMA,
    params={"n": 10},
    bind={"values": "kline.close"},
)
```

优点：

- 稳定、显式、可序列化。
- 真实参数名与 pyta2 一致，便于复现和网格搜索。
- 适合 Agent、配置文件和批量生成。

缺点：

- 普通用户需要知道 pyta2 类名、构造参数和 `forward()` 参数名。
- 高频场景样板代码偏多。

### 方案 B：只暴露用户 DSL

示例：

```python
features = [
    SMA("close", window=10),
    ATR(window=14),
    MACD("close", fast=12, slow=26, signal=9),
]
```

优点：

- 上手快，符合用户心智。
- 适合 notebook 和业务快速试验。

缺点：

- 容易隐藏真实参数名和绑定规则。
- 复杂组合 feature、输出重命名、namespace、外部数据源扩展会变得不透明。

### 方案 C：双层 API

同时提供稳定底层 `FeatureSpec` 和高层 DSL。DSL 只负责展开为 `FeatureSpec`。

优点：

- 简单场景短，复杂场景清楚。
- `FeatureSpec` 是稳定内部/配置边界，DSL 是用户友好入口。
- 既支持手写特征，也支持程序化批量生成。

缺点：

- 需要维护 DSL 展开测试，防止 DSL 与底层规范漂移。

### 结论

采用方案 C。

公共稳定接口以 `rSignal`、数据类型专属信号、`SignalEngine` 和 DSL 构造器为核心。`FeatureSpec` 可作为后续矩阵输出或声明式配置对象保留，但不再是 sigma2 的第一核心抽象。`rPyta2Signal`、`SignalNode`、`PathBufferStore` 等内部接口不承诺公共兼容性。

## 定稿 API

此处原先以 `FeatureSpec` 为主的 API 已被 `docs/design/sigma2-20260704-signal-core.md` 修订。后续实现应先实现 `rSignal` 标准信号接口，再实现 pyta2 适配和声明式配置。

### rSignal 与 rKlineSignal

```python
class rSignal:
    data_kind: str | None = None

    def rolling(self, *args, **kwargs):
        ...

    def update(self, *args, **kwargs):
        ...

class rKlineSignal(rSignal):
    data_kind = "kline"

    def forward(self, opens, highs, lows, closes, volumes):
        ...

    def update(self, open, high, low, close, volume):
        ...
```

约束：

- `rSignal` 固定生命周期和输出契约，不固定输入字段。
- `rKlineSignal` 的 rolling 序列输入固定为 `opens, highs, lows, closes, volumes`。
- `rKlineSignal` 的单点更新输入固定为 `open, high, low, close, volume`。
- 未来 `rOrderBookSignal`、`rTradeSignal` 分别定义自己的标准输入。
- 输出必须通过 `schema` 映射为稳定 dict。
- pyta2 指标通过 `rPyta2Signal` 接入，而不是让用户直接围绕 pyta2 `forward()` 参数写绑定。

### SignalEngine

```python
engine = SignalEngine(signals)

row = engine.update(
    kline={
        "open": 101.0,
        "high": 103.0,
        "low": 100.0,
        "close": 102.0,
        "volume": 1200.0,
    }
)

latest = engine.latest()
matrix = engine.batch(kline_df)
```

如果 engine 中全是 K 线信号，可以额外提供便捷形式：

```python
engine.update(open=101.0, high=103.0, low=100.0, close=102.0, volume=1200.0)
```

行为：

- 初始化时完成 pyta2 实例化、输入签名校验、输出列推导、DAG 构建、buffer 需求计算。
- `update()` 追加外部路径值，按拓扑顺序计算 feature，并返回当前输出行。
- `latest()` 返回最近一次完整输出行。
- `batch()` 按输入时间轴逐行 replay `update()`，返回与历史数据对齐的矩阵。

### DSL

DSL 是用户接口，不是底层规范：

```python
features = [
    SMA("close", window=10),
    SMA("close", window=20),
    ATR(window=14),
    MACD("close", fast=12, slow=26, signal=9),
]
```

展开后的底层声明仍然使用真实 pyta2 参数：

```python
FeatureSpec(
    name="macd_close",
    cls=rMACD,
    params={"n1": 26, "n2": 12, "n3": 9},
    bind={"values": "kline.close"},
)
```

## 路径与命名规则

外部行情路径：

- `kline.open`
- `kline.high`
- `kline.low`
- `kline.close`
- `kline.volume`
- `orderbook.bid_price_1`
- `orderbook.ask_price_1`
- `trades.price`
- `trades.volume`

内部 feature 路径：

- 规范路径：`<namespace>.<feature_name>.<output_key>`
- 单输出短路径：`<namespace>.<feature_name>`
- 多输出 feature 必须显式指定输出键。

输出列名：

- 单输出默认列名为 `FeatureSpec.name`。
- 多输出默认列名为 `{FeatureSpec.name}_{output_key}`。
- 显式 `outputs` 只影响最终矩阵列名，不影响内部依赖路径。

## 内部架构

建议包结构：

```text
sigma2/
├── __init__.py
├── adapter.py
├── buffers.py
├── dsl.py
├── engine.py
├── errors.py
├── graph.py
├── paths.py
└── specs.py
tests/
├── test_adapter.py
├── test_batch_replay.py
├── test_dsl.py
├── test_engine_update.py
├── test_graph.py
└── test_specs.py
```

内部组件：

- `Pyta2Adapter`：实例化 pyta2 指标，读取元信息，校验 `bind`，执行 `rolling()`。
- `FeatureNode`：保存 spec、adapter、输出路径、输出列、依赖路径和窗口信息。
- `FeatureGraph`：解析依赖、检测环、拓扑排序、计算 `effective_required_window`。
- `PathBufferStore`：按路径共享 buffer，外部行情和内部 feature 使用同一抽象。
- `FeatureEngine`：协调数据写入、节点执行、输出行组装和 batch replay。

错误类型：

- `SigmaError`
- `SpecValidationError`
- `PathValidationError`
- `GraphCycleError`
- `DuplicateOutputError`
- `MissingInputError`

## 实施阶段

### P0：规划和项目骨架

- 补齐 README、设计文档、计划索引和交接文档。
- 创建 Python 包骨架、`pyproject.toml` 和测试框架。

验收：

- 新 agent 能通过文档理解项目目标、边界和下一步。
- `pytest` 可以运行空测试或基础导入测试。

### P1：FeatureSpec 与 Pyta2Adapter

- 实现 `FeatureSpec`。
- 实现输出列推导。
- 实现 `forward()` 签名检查。
- 使用 `buffer_size=1`、`return_dict=True` 实例化 pyta2 指标。
- 覆盖 rSMA、rATR、rMACD 的 adapter 测试。

验收：

- 单输出、多输出、显式重命名全部通过测试。
- 缺少 bind、未知 bind、错误 outputs 均在初始化时报错。

### P2：路径、DAG 与 warmup

- 实现路径解析。
- 区分外部路径和内部 feature 路径。
- 支持单输出短路径别名。
- 构建 feature DAG 并做拓扑排序。
- 计算 `effective_required_window`。

验收：

- MACD 后接 SMA 的组合 feature 可正确排序。
- 循环依赖、未知内部路径、重复输出路径可稳定报错。

### P3：rolling engine

- 实现共享 buffer。
- 实现 `FeatureEngine.update()` 和 `latest()`。
- 按拓扑顺序执行节点。
- 组装最新输出行。

验收：

- SMA、ATR、MACD 和组合 feature 可逐 tick 更新。
- 多个 feature 共享 `kline.close` buffer。
- 输出列与设计规则一致。

### P4：batch replay

- 实现 `FeatureEngine.batch()`。
- 支持 pandas DataFrame 和基础 dict/list 输入中的一个最小版本。
- batch 内部复用 `update()`。

验收：

- `batch(history)` 与手动循环 `update(row)` 输出一致。
- 返回矩阵与输入时间轴对齐，不默认 drop warmup。

### P5：DSL 与文档示例

- 实现 `SMA()`、`ATR()`、`MACD()`。
- DSL 只展开为 `FeatureSpec`。
- 补充 README 示例和端到端测试。

验收：

- 用户可以用 3 到 5 行完成常见 feature 矩阵生成。
- DSL 展开结果有快照测试，避免后续漂移。

### P6：优化与扩展

- 对无内部依赖子图考虑批量优化。
- 增加更多 pyta2 指标 DSL。
- 增加配置文件加载、spec 序列化和更完整的数据源适配。

验收：

- 优化路径必须通过 batch/rolling 一致性测试。
- 新 DSL 不改变 `FeatureSpec` 核心契约。

## 查漏补缺

### 第一轮：与 pyta2 职责边界

风险：sigma2 重新发明指标 registry，导致 output/schema/window 双重维护。

结论：只保留薄 `Pyta2Adapter`，所有指标元信息从实例读取。

### 第二轮：用户 API 与内部 API 边界

风险：为了方便用户，把内部 buffer、节点和 graph 细节暴露为公共接口。

结论：公共接口只承诺 `FeatureSpec`、`FeatureEngine` 和 DSL。内部组件可以测试但不作为稳定 API。

### 第三轮：batch 与 rolling 一致性

风险：过早调用 pyta2 batch 函数拼接矩阵，导致组合 feature 和实时 rolling 语义不一致。

结论：默认 batch 必须 replay `update()`。性能优化后置，并以一致性测试为准入条件。

## 优先级判断

当前最高优先级不是实现大量 DSL，而是先完成最小正确核心：

1. `FeatureSpec` 能准确表达 pyta2 指标调用。
2. `Pyta2Adapter` 能从 pyta2 实例读取事实元信息。
3. 路径绑定、输出命名和错误语义稳定。
4. rolling engine 可跑通单指标和一个组合指标。

完成这四点后，sigma2 才具备可演进基础。
