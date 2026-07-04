# sigma2 系统设计稿

更新时间：2026-07-04 15:50 CST

## 状态

本文是当前推荐的系统设计稿，用于替代早期“pyta2 适配优先”和“直接暴露 KlineInput”等方向。早期文档仍保留历史讨论价值，但后续实现应以本文为主。

## 背景

sigma2 的核心场景不是回测框架适配，而是机器学习方法开发量化交易策略：

1. 用户已有历史行情、订单簿、成交、新闻等数据。
2. 用户声明一组信号或特征。
3. sigma2 生成训练矩阵。
4. 用户训练模型、做特征分析、调参。
5. 同一组信号可在回测或实盘中在线更新。

因此，sigma2 不应让普通用户介入 `KlineInput`、`OrderBookInput` 等较重的内部对象，也不应为了兼容 minbt 使用 `bar/bars` 作为核心词汇。minbt 是一个适配目标，sigma2 内部应使用自洽的量化数据语义。

## 总目标

sigma2 是面向量化 ML 的信号与特征生成库。

用户主路径：

```python
features = FeatureSet([
    kline.ret(1),
    kline.ret(5),
    kline.sma("close", 20),
    orderbook.spread(level=1),
    orderbook.imbalance(depth=5),
    trade.vwap(window=100),
])

X = features.batch(data)
```

在线策略主路径：

```python
state = features.online()
row = state.update_kline(symbol="BTCUSDT", dt=dt, open=o, high=h, low=l, close=c, volume=v)
```

minbt 适配主路径：

```python
from sigma2.adapters.minbt import MinbtFeatureAdapter

def on_bars(self, dt, bars):
    rows = self.sigma.update_bars(dt, bars)
```

## 非目标

- 不做交易、下单、持仓、资金管理，这些属于 minbt 或其它交易框架。
- 不把 minbt 的 `bar/bars` 命名带入 sigma2 核心。
- 不要求普通用户手工构造 `KlineInput`、`OrderBookInput`、`TradeInput`。
- 不把 pyta2 作为 sigma2 的唯一核心。pyta2 是 rolling 指标内核来源之一。
- 不在第一阶段追求所有 batch 计算向量化。接口上 batch 是一等主路径，实现上可先 replay rolling。

## 设计原则

### 用户接口

用户接口贴近真实意图：

- 声明我要哪些特征。
- 给一份数据，生成训练矩阵。
- 在在线策略里推进一次状态，拿到当前特征。

用户接口应尽量少暴露：

- 输入标准化对象。
- buffer。
- DAG 节点。
- pyta2 `forward()` 参数名。
- 不同框架的回调细节。

### 内部接口

内部接口必须契约完整：

- 每种输入类型有明确字段、时间语义、symbol 语义。
- 每个 rolling 信号有明确状态生命周期。
- batch 与 online 的输出列名、时间对齐、warmup 语义一致。
- 跨信号依赖必须可拓扑排序和检测环。

## 核心概念

### FeatureSet

`FeatureSet` 是普通用户主入口。

```python
features = FeatureSet([...])
X = features.batch(data)
state = features.online()
```

职责：

- 接收用户声明的信号。
- 识别数据 schema。
- 调用内部标准化层。
- 输出训练矩阵。
- 创建在线状态对象。

### rSignal

`rSignal` 中的 `r` 表示 rolling。它是有状态 rolling 信号内核，区别于纯 batch 计算函数。

`rSignal` 面向库开发者、高级用户和内部实现，不是普通 ML 用户的第一入口。

职责：

- 生命周期：`reset()`、`update(...)`。
- 输出：`schema`、`output_keys`、`make_dict_output()`。
- 缓存：`outputs`。
- 元信息：`name`、`full_name`、`window`、`required_window`、`family`。

`rSignal` 不负责定义具体输入字段。输入字段由 signal family 决定。

### Signal family

Signal family 由输入类型决定。这是二次开发的核心扩展轴。

设计关系：

```text
InputType -> SignalFamily -> Signal
```

单 symbol 和多 symbol 必须区分，因为它们的状态、输出和 ML 对齐语义不同。

第一批 family：

| family | 输入语义 | 示例信号 |
| --- | --- | --- |
| `kline` | 单 symbol K 线时间序列 | `KlineReturn`、`KlineSMA`、`KlineATR` |
| `multi_kline` | 多 symbol K 线截面或多 symbol 时间序列 | `CrossSectionRank`、`PairSpread`、`MarketBreadth` |
| `orderbook` | 单 symbol 订单簿快照时间序列 | `OrderBookSpread`、`OrderBookImbalance` |
| `multi_orderbook` | 多 symbol 订单簿截面 | `CrossSectionLiquidityRank` |
| `trade` | 单 symbol 成交流或成交批次 | `TradeVWAP`、`TradeVolumeSum` |
| `multi_trade` | 多 symbol 成交截面或批次 | `MarketFlowImbalance` |
| `composite` | 已有信号输出 | `EntryScore`、`RegimeFilter` |
| `label` | 未来收益或训练目标 | `FutureReturn`、`ForwardMaxDrawdown` |

扩展规则：

- 新增数据类型时，新增 `InputType`、normalizer、family module 和信号实现。
- `FeatureSet` 和 `OnlineFeatureState` 不应因为新增 family 修改核心逻辑。
- family 通过 registry 注册，而不是在核心流程里写死 `if family == "kline"`。
- 便捷方法可以为常见 family 提供，但扩展不依赖便捷方法。

新增 funding rate 的目标形态：

```python
registry.register_family(
    family="funding_rate",
    input_type=FundingRateInput,
    normalizer=FundingRateNormalizer,
)

features = FeatureSet([
    funding_rate.current(),
    funding_rate.zscore(window=24),
])
```

### 内部输入类型

内部输入类型用于标准化数据，不是普通用户主接口。

示意：

```python
KlineInput
MultiKlineInput
OrderBookInput
MultiOrderBookInput
TradeInput
MultiTradeInput
SignalInput
```

这些对象由 `FeatureSet.batch(data, schema=...)`、`OnlineFeatureState.update_*()` 或 adapter 自动构造。高级用户可以直接使用它们，但文档主路径不要求。

输入类型契约要求：

- 必须声明所属 `family`。
- 必须包含时间语义。
- 单 symbol 输入必须包含 `symbol`。
- 多 symbol 输入必须明确输出是一行多列、还是每个 symbol 一行。
- 必须能被 normalizer 从用户数据或 adapter 数据构造。

## Family Registry

`FamilyRegistry` 是内部扩展机制，不是普通用户第一入口。

职责：

- 根据 family 找到输入类型。
- 根据 family 找到 normalizer。
- 根据 family 找到默认 online update 路由。
- 根据 family 找到信号运行器和 batch replay 规则。

伪接口：

```python
class FamilyRegistry:
    def register(self, family, input_type, normalizer, runner=None):
        ...

    def get(self, family):
        ...
```

核心要求：

- `FeatureSet.batch(...)` 只依赖 registry，不依赖具体 family 分支。
- `OnlineFeatureState.update(input_obj)` 只依赖 `input_obj.family` 路由。
- `OnlineFeatureState.update_family(family, **data)` 通过 registry 构造 input。
- `update_kline(...)`、`update_orderbook(...)` 等只是便捷包装。

推荐在线核心接口：

```python
state.update(input_obj)
state.update_family("kline", symbol="BTCUSDT", dt=dt, open=o, high=h, low=l, close=c, volume=v)
```

便捷接口：

```python
state.update_kline(symbol="BTCUSDT", dt=dt, open=o, high=h, low=l, close=c, volume=v)
```

扩展 family 不应要求修改 `OnlineFeatureState` 类；最多新增独立便捷函数或 adapter。

## 用户接口方案比较

### 方案 A：用户直接构造输入对象

```python
rows = [
    KlineInput(symbol="BTCUSDT", dt=dt, open=o, high=h, low=l, close=c, volume=v),
]
X = features.batch(rows)
```

优点：

- 类型契约清楚。
- 适合内部测试和高级适配器。

缺点：

- 对 ML 用户过重。
- 用户已有 DataFrame 时需要大量样板代码。
- 暴露内部标准化细节。

结论：作为高级接口保留，不作为主路径。

### 方案 B：用户只传 DataFrame，自动推断字段

```python
X = features.batch(df)
```

优点：

- 最短路径好用。
- 贴近 ML 用户习惯。

缺点：

- 字段不标准时需要清晰错误。
- 多数据类型混合时需要 schema 显式化。

结论：作为最常见主路径采用。

### 方案 C：DataFrame + 显式 DataSchema

```python
X = features.batch(
    df,
    schema=DataSchema(
        time="timestamp",
        symbol="instrument",
        kline={"open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"},
    ),
)
```

优点：

- 适合真实生产数据。
- 字段映射显式，不靠魔法。
- 仍不要求用户构造输入对象。

缺点：

- 多一点配置。

结论：作为复杂场景主路径采用。

### 综合方案

采用 B + C + A 的渐进式复杂：

1. 标准字段自动推断。
2. 非标准字段使用 `DataSchema`。
3. 高级用户和 adapter 可直接使用内部输入对象。

## 数据接口

### DataSchema

`DataSchema` 描述原始数据到 sigma2 内部输入类型的字段映射。

```python
schema = DataSchema(
    time="dt",
    symbol="symbol",
    available_time=None,
    kline={
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    },
    orderbook={
        "bids": "bids",
        "asks": "asks",
    },
    trade={
        "price": "price",
        "volume": "volume",
        "side": "side",
    },
)
```

默认约定：

- `time`: `dt`
- `symbol`: `symbol`
- K 线字段：`open/high/low/close/volume`
- orderbook 字段：`bids/asks`，或后续支持展开档位列。
- trade 字段：`price/volume/side`

### 时间语义

ML 场景必须防未来函数。

所有内部输入都应支持：

- `dt`：数据所属时间。
- `symbol`：标的。
- `available_time`：该数据何时可用于决策。

默认：

- 用户未提供 `available_time` 时，等于 `dt`。
- 对 K 线，后续可通过 schema 或 frequency 指定 close bar 的可用时间规则。

### 输出矩阵

`FeatureSet.batch(data)` 默认输出训练友好的表：

```text
dt | symbol | feature columns...
```

列名规则：

- 单输出信号：`ret_5`
- 多输出信号：`macd.dif`、`macd.dea`、`macd.macd`
- family 可作为可选前缀：`kline.ret_5`、`orderbook.spread_1`

是否加 family 前缀应可配置：

```python
FeatureSet(signals, column_style="short")
FeatureSet(signals, column_style="family")
```

## rSignal 内部接口

建议接口：

```python
class rSignal:
    name: str
    family: str

    def update(self, input):
        ...

    def reset(self):
        ...

    @property
    def outputs(self):
        ...

    @property
    def meta_info(self):
        ...
```

不推荐把 `rolling(...)` 作为主方法名。原因：

- `rolling` 容易混淆“输入一个窗口”、“推进一个点”和“对整段历史 rolling transform”。
- `rSignal` 的 `r` 已经表达 rolling、有状态。
- 用户主路径是 `batch(data)` 和 `online().update_*()`。

推荐：

- `update(input)`：rolling 状态推进一个输入。
- `compute(input)` 或内部 `_compute(input)`：基于当前状态计算一次输出。
- `batch(data)`：属于 `FeatureSet`，不是单个 `rSignal` 的主用户接口。

如需兼容 pyta2 心智，可提供：

```python
rolling = update
```

但文档主路径不推荐。

## 批量特征生成

`FeatureSet.batch(...)` 是核心场景，不是在线模式的附属能力。

第一版实现可以 replay `rSignal.update(...)`：

```text
data -> normalize -> sorted inputs -> update signals -> rows
```

后续优化可以对无依赖信号使用向量化实现，但必须满足：

```text
FeatureSet.batch(data) == replay(FeatureSet.online().update_*(...))
```

重要参数：

```python
X = features.batch(
    data,
    schema=None,
    sort=True,
    drop_warmup=False,
    include_time=True,
    include_symbol=True,
)
```

warmup 策略：

- 默认不裁剪。
- 输出 NaN 或信号自然无效值。
- 裁剪、对齐标签、训练样本过滤属于 ML 后处理，可提供辅助函数但不默认隐藏。

## 在线特征状态

`FeatureSet.online()` 返回 `OnlineFeatureState`。

```python
state = features.online()

row = state.update_kline(
    symbol="BTCUSDT",
    dt=dt,
    open=o,
    high=h,
    low=l,
    close=c,
    volume=v,
)
```

多 symbol 截面：

```python
rows = state.update_kline_frame(dt=dt, data=rows_by_symbol)
```

orderbook：

```python
row = state.update_orderbook(
    symbol="BTCUSDT",
    dt=dt,
    bids=[(100.0, 1.2)],
    asks=[(100.1, 0.9)],
)
```

trade：

```python
row = state.update_trade(symbol="BTCUSDT", dt=dt, price=100.0, volume=1.2, side="buy")
```

`OnlineFeatureState` 负责：

- 按 family 和 symbol 管理 `rSignal` 实例。
- 把用户轻量输入转换为内部输入对象。
- 汇总当前输出行。
- 支持与 minbt、实盘框架适配。

扩展约束：

- 核心必须提供 `update(input_obj)`。
- 核心必须提供 `update_family(family, **data)`。
- `update_kline(...)` 是内置 family 的便捷方法，不是扩展机制本身。
- 新增 family 通过 registry 加入，不应修改 `OnlineFeatureState` 的核心路由。

## 组合信号

组合信号以已有信号输出为输入，而不是直接消费原始行情。

```python
entry_score = composite.score(
    name="entry_score",
    inputs=["kline.ret_5", "orderbook.spread_1", "trade.vwap_100"],
    fn=lambda x: x["kline.ret_5"] - x["orderbook.spread_1"],
)
```

内部要求：

- 解析依赖。
- 拓扑排序。
- 检测循环依赖。
- 传播 warmup。
- 保证 batch 与 online 一致。

## pyta2 关系

pyta2 是 rolling 指标内核来源之一。

适配方式：

```python
kline.pyta2(
    name="macd",
    indicator_cls=rMACD,
    params={"n1": 26, "n2": 12, "n3": 9},
    input_map={"values": "close"},
)
```

普通用户更推荐：

```python
kline.macd("close", fast=12, slow=26, signal=9)
```

适配层规则：

- 输出键、schema、窗口从 pyta2 实例读取。
- sigma2 不重复维护 pyta2 指标定义。
- pyta2 当前不允许 `buffer_size=0`，短期适配使用 `buffer_size=1`。

## minbt 关系

minbt 是回测运行时和交易执行框架，sigma2 是信号状态层。

边界：

- sigma2 不调用 `Broker`。
- sigma2 不提交订单。
- minbt 不负责信号计算。
- Strategy 负责把 sigma2 输出转成交易意图。

适配层：

```python
from sigma2.adapters.minbt import MinbtFeatureAdapter
```

示例：

```python
class AlphaStrategy(Strategy):
    def on_init(self):
        self.state = FeatureSet([
            kline.ret(5),
            kline.sma("close", 20),
            orderbook.spread(1),
        ]).online()
        self.sigma = MinbtFeatureAdapter(self.state)

    def on_bars(self, dt, bars):
        rows = self.sigma.update_bars(dt, bars)
        for symbol, f in rows.items():
            price = bars[symbol]["close"]
            target = 0.5 if f["ret_5"] > 0 and price > f["sma_20"] else 0.0
            self.broker.order_target_percent(symbol, target, price=price)
```

minbt 的 `bars/books/trades/news` 命名只出现在 adapter 边界，sigma2 核心仍使用 `kline/orderbook/trade/news`。

硬规则：

- `FeatureSet`、`OnlineFeatureState`、`rSignal` 不能出现 `minbt`、`backtrader`、`zipline` 等外部框架名。
- 外部框架适配只能存在于 `sigma2.adapters.*`。
- adapter 只翻译数据，不调用 broker，不提交订单。
- `update_minbt_bars(...)` 这类方法不得出现在 core 对象上。

## 标签与训练目标

ML 场景需要 label 作为一等概念，但 label 不应和普通信号混淆。

推荐：

```python
y = LabelSet([
    label.future_return(horizon=5),
]).batch(data)
```

label 规则：

- 默认输出未来信息，只能用于训练集生成。
- 在线状态不允许计算未来 label。
- 与 feature 对齐时必须显式指定 horizon 和 available_time 规则。

## 包结构建议

```text
sigma2/
├── __init__.py
├── data/
│   ├── schema.py
│   ├── inputs.py
│   └── normalize.py
├── signal/
│   ├── base.py
│   ├── kline.py
│   ├── multi_kline.py
│   ├── orderbook.py
│   ├── trade.py
│   └── composite.py
├── features/
│   ├── set.py
│   ├── online.py
│   └── matrix.py
├── adapters/
│   ├── pyta2.py
│   └── minbt.py
└── errors.py
```

公共入口：

```python
from sigma2 import FeatureSet, DataSchema
from sigma2 import kline, orderbook, trade, composite, label
```

## 第一批信号

### kline

- `kline.ret(horizon=1)`
- `kline.sma(field="close", window=20)`
- `kline.volatility(field="close", window=20)`
- `kline.macd(field="close", fast=12, slow=26, signal=9)`

### multi_kline

- `multi_kline.rank(input="kline.ret_5")`
- `multi_kline.pair_spread(symbol_a, symbol_b, field="close")`
- `multi_kline.market_breadth(condition=...)`

### orderbook

- `orderbook.mid_price(level=1)`
- `orderbook.spread(level=1)`
- `orderbook.imbalance(depth=5)`

### trade

- `trade.vwap(window=100)`
- `trade.volume_sum(window=100)`
- `trade.flow_imbalance(window=100)`

### label

- `label.future_return(horizon=5)`
- `label.future_max_drawdown(horizon=20)`

## 查漏补缺

### 第一轮：用户是否需要理解 KlineInput

不需要。普通用户主路径是 DataFrame、DataSchema、FeatureSet。`KlineInput` 是内部标准化对象。

### 第二轮：batch 是否被降级为 replay 附属

不会。`FeatureSet.batch(data)` 是主入口。第一版可用 replay 实现，但接口和测试必须把 batch 作为一等能力。

### 第三轮：rSignal 是否和 batch 混淆

不会。`rSignal` 中 `r` 明确表示 rolling、有状态。batch 是 `FeatureSet` 的能力，可以调用 rolling replay，也可以走专用 batch kernel。

### 第四轮：单 symbol 与多 symbol 是否混淆

不混淆。`kline` 与 `multi_kline` 是不同 family。前者输出单 symbol 特征，后者处理截面或跨 symbol 关系。

### 第五轮：minbt 是否污染 sigma2 命名

不污染。minbt 的 `bars` 只在 `adapters.minbt` 边界出现，sigma2 核心使用 `kline`。

### 第六轮：新增数据类型是否需要改核心

不需要。新增数据类型应通过 `InputType + Normalizer + family module + registry` 加入。核心 `FeatureSet` 和 `OnlineFeatureState` 只依赖 registry，不写死具体 family。

## 实施优先级

1. 建立包骨架、错误类型和最小测试。
2. 实现 `FeatureSet.batch(data)` 的最小 kline 路径。
3. 实现 `DataSchema` 自动推断和显式字段映射。
4. 实现 `rSignal`、`rKlineSignal` 内核，但不把它作为用户主文档入口。
5. 实现 `kline.ret`、`kline.sma`。
6. 实现 `FeatureSet.online()` 和 `update_kline(...)`。
7. 实现 orderbook/trade 的输入标准化和简单信号。
8. 实现 `FamilyRegistry`，把 kline/orderbook/trade 都通过 registry 注册。
9. 实现 pyta2 适配。
10. 实现 minbt adapter。
11. 实现 composite 与 label。
