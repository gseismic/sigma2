# sigma2 标准信号核心设计

更新时间：2026-07-04 16:31 CST

> 历史备份：本文是阶段性核心设计，不作为当前实现依据。当前唯一有效设计见 `docs/design/sigma2-20260704-overview.md`。

## 状态

本文是早期核心修订文档，保留历史讨论价值。后续实现以 `docs/design/sigma2-20260704-overview.md` 为准：公共稳定命名采用 `family`，`rSignal` 的概念、命名、生命周期和默认行为应尽可能与 `pyta2.base.rIndicator` 保持一致。

## 背景

上一版规划过于围绕 `FeatureSpec + Pyta2Adapter`，容易把 sigma2 做成 pyta2 的封装层。用户明确要求：

- sigma2 不仅封装 pyta2。
- sigma2 要能组合 pyta2 指标。
- sigma2 要能自定义信号。
- sigma2 总体结构应与 `pyta2.base.rIndicator` 类似，最好保持一致。
- 与 pyta2 的主要差异是标准化输入和输出。
- 对 K 线，rolling 模式输入固定为 `opens, highs, lows, closes, volumes`。
- 对单点更新模式，每次输入固定为 `open, high, low, close, volume`。
- K 线只是其中一种数据类型，未来还要扩展 orderbook、trades 等数据。

因此，sigma2 的核心抽象应从“pyta2 指标绑定声明”调整为“标准信号对象”，并且输入标准化必须按数据类型分层：通用 `rSignal` 不锁定输入字段，`rKlineSignal`、`rOrderBookSignal` 等子类分别定义自己的标准输入。

## 设计目标

- 提供通用 `rSignal` 基类，结构尽量接近 `pyta2.base.rIndicator`。
- `rSignal` 负责生命周期、schema、输出缓存、`meta_info` 和错误语义。
- 数据输入契约由 data-kind 子类负责，例如 `rKlineSignal`、未来的 `rOrderBookSignal`。
- 用户可以继承 `rKlineSignal` 编写 K 线自定义信号，未来也可以继承其它数据类型信号。
- pyta2 指标通过 `rPyta2Signal` 适配为 K 线信号。
- 组合信号可以在内部复用 pyta2 指标、sigma2 信号和普通 Python 逻辑。
- rolling 和单点 update 使用同一套状态与输出语义。
- 输出必须标准化为 schema 驱动的 dict，适合实时使用和 ML 矩阵生成。

## 非目标

- 不要求所有信号都来自 pyta2。
- 不要求用户理解 pyta2 指标的 `forward()` 参数名。
- 不在第一阶段实现所有行情源。第一阶段只实现 K 线 OHLCV，但架构必须保留 orderbook/trades 的 data-kind 扩展口。
- 不把 `FeatureSpec` 作为第一公共抽象。它可以后续作为序列化配置或矩阵列声明。

## 接口方案比较

### 方案 A：FeatureSpec 继续作为核心

示例：

```python
FeatureSpec(
    name="atr14",
    cls=rATR,
    params={"n": 14},
    bind={"highs": "kline.high", "lows": "kline.low", "closes": "kline.close"},
)
```

优点：

- 声明式，便于序列化。
- 适合把 pyta2 指标接入矩阵生成。

缺点：

- 用户仍然围绕 pyta2 的 `forward()` 参数思考。
- 自定义信号没有自然位置。
- sigma2 会被限制成 pyta2 的编排壳。

结论：不作为第一核心抽象。

### 方案 B：rSignal 直接固定 OHLCV

示例：

```python
class rGapSignal(rSignal):
    name = "Gap"

    def __init__(self, **kwargs):
        super().__init__(
            window=2,
            schema=[("gap", Box(low=-float("inf"), high=float("inf")))],
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes):
        if len(opens) < 2:
            return float("nan")
        return opens[-1] - closes[-2]
```

优点：

- 与 pyta2 的 `rIndicator` 心智一致。
- 自定义信号、组合信号和 pyta2 适配都可以落在同一个对象模型里。
- K 线输入契约稳定，用户不用理解每个 pyta2 指标的内部输入名。

缺点：

- 后续仍需额外设计信号图、矩阵列名和声明式配置。
- 会把 `rSignal` 锁死为 K 线，阻碍 orderbook/trades 扩展。

结论：不直接采用，但保留其 K 线部分，沉到 `rKlineSignal`。

### 方案 C：rSignal 通用生命周期 + data-kind 子类

优点：

- 能同时保持 `rIndicator` 一致的对象模型和 K 线固定签名。
- K 线、orderbook、trades 可以分别拥有清晰输入契约。
- 第一阶段只实现 `rKlineSignal`，但不会把未来扩展堵死。

缺点：

- 比单一 `rSignal` 多一个抽象层。
- `SignalEngine` 需要按 `data_kind` 路由输入。

结论：采用。

### 方案 D：一开始设计通用多行情源 SignalFrame

优点：

- 能同时覆盖 kline、orderbook、trades 等数据源。

缺点：

- 第一阶段复杂度过高。
- 可能稀释用户当前明确提出的 K 线 OHLCV 标准输入契约。

结论：暂缓。第一阶段先做 `rSignal + rKlineSignal`，未来根据 orderbook 实际需求再设计 `rOrderBookSignal` 或 `SignalFrame`。

## 定稿：rSignal 与 data-kind 子类

`rSignal` 是 sigma2 的通用核心基类，生命周期、命名和元信息应尽量与 `pyta2.base.rIndicator` 保持一致。它不规定具体行情输入字段。

```python
class rSignal:
    name: str | None = None
    data_kind: str | None = None

    def __init__(
        self,
        window: int,
        schema,
        *,
        buffer_size: int | None = None,
        extra_window: int = 0,
        buffer_factor: int = 2,
        return_dict: bool = False,
    ):
        ...

    def rolling(self, *args, **kwargs):
        ...

    def update(self, *args, **kwargs):
        ...

    def forward(self, *args, **kwargs):
        raise NotImplementedError

    def reset(self):
        ...

    def reset_extras(self):
        ...
```

字段与行为：

- `window`：信号自身结构窗口。
- `extra_window`：额外窗口。
- `required_window`：`window + extra_window`。
- `schema`：输出字段定义，建议复用 pyta2 的 `Schema`/`Space` 模型以保持一致。
- `output_keys`：来自 `schema.keys()`。
- `return_dict`：默认值与 `rIndicator` 保持一致；标准化输出由 `schema`、`output_keys` 和 `make_dict_output()` 保证，应用层需要 dict 时显式传入 `return_dict=True`。
- `outputs`：历史输出缓存。
- `meta_info`：包含 `name`、`full_name`、`schema`、`window`、`extra_window`、`required_window`、`output_keys` 等。

## K 线标准输入：rKlineSignal

`rKlineSignal` 是第一阶段必须实现的数据类型专属基类。

```python
class rKlineSignal(rSignal):
    data_kind = "kline"
    rolling_input_keys = ("opens", "highs", "lows", "closes", "volumes")
    update_input_keys = ("open", "high", "low", "close", "volume")

    def rolling(self, opens, highs, lows, closes, volumes):
        ...

    def update(self, open, high, low, close, volume):
        ...

    def forward(self, opens, highs, lows, closes, volumes):
        raise NotImplementedError
```

### rolling 序列输入

所有 K 线信号的 `forward()` 和 `rolling()` 输入固定为：

```python
signal.rolling(opens, highs, lows, closes, volumes)
```

约束：

- 五个输入必须长度一致。
- 输入是窗口序列，不是单个值。
- 子类只从这些标准序列中取需要的字段。
- 不允许用户在 K 线信号里暴露 `values`、`highs/lows/closes` 这类 pyta2 局部概念。

### 单点更新输入

实时模式每次只输入一个 K 线点：

```python
signal.update(open, high, low, close, volume)
```

行为：

- `update()` 把单点追加到内部 OHLCV buffer。
- `update()` 再委托 `rolling(opens, highs, lows, closes, volumes)`，由 `rolling()` 统一推进 `g_index`、调用 `forward()`、写入 `outputs` 并处理 `return_dict`。
- 因此单点模式和 rolling 序列模式共享同一份计算语义。

### Python 命名说明

`open` 会遮蔽 Python 内置函数名，但它是用户最熟悉的行情字段名。公共 API 可以接受 `open` 作为关键字；内部实现可以使用 `open_` 变量承接，避免误用内置函数。

## 未来数据类型扩展

orderbook、trades 等不应塞进 `rKlineSignal`，也不应迫使所有信号使用一个过度泛化的 `data` 参数。推荐模式是为每类行情定义一个 data-kind 子类。

未来示意：

```python
class rOrderBookSignal(rSignal):
    data_kind = "orderbook"

    def rolling(self, snapshots):
        ...

    def update(self, snapshot):
        ...

    def forward(self, snapshots):
        raise NotImplementedError
```

也可以在 orderbook 设计成熟后选择更展开的输入，例如 bid/ask 多档价格和数量数组。当前不提前锁定字段，只锁定扩展原则：

- 每个 data-kind 子类必须有明确、稳定的 rolling/update 输入契约。
- 同一 data-kind 下的信号不得各自发明不同输入名。
- `SignalEngine` 按 `data_kind` 路由输入。
- 标准输出仍由 `rSignal` 的 schema 和 `make_dict_output()` 统一处理。

## 标准输出

输出沿用 pyta2 的 schema 思路：

- 单输出信号可以返回标量。
- 多输出信号可以返回 tuple/list 或 mapping。
- `rSignal` 统一通过 `make_dict_output()` 转成 dict。
- dict key 必须等于 `output_keys`。

示例：

```python
class rReturnSignal(rKlineSignal):
    name = "Return"

    def __init__(self, n=1, **kwargs):
        self.n = n
        super().__init__(
            window=n + 1,
            schema=[("ret", Box(low=-float("inf"), high=float("inf")))],
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes):
        if len(closes) <= self.n:
            return float("nan")
        return closes[-1] / closes[-1 - self.n] - 1.0
```

## pyta2 适配

pyta2 适配不再是 sigma2 核心，而是 `rKlineSignal` 的一个子类或组合工具。

```python
rPyta2Signal(
    name="sma10_close",
    indicator_cls=rSMA,
    params={"n": 10},
    input_map={"values": "closes"},
)
```

ATR 示例：

```python
rPyta2Signal(
    name="atr14",
    indicator_cls=rATR,
    params={"n": 14, "ma_type": "EMA"},
    input_map={
        "highs": "highs",
        "lows": "lows",
        "closes": "closes",
    },
)
```

约束：

- `rPyta2Signal` 自身对外仍然是 `forward(opens, highs, lows, closes, volumes)`。
- `input_map` 是适配层内部概念，不应成为普通用户最常写的接口。
- `rPyta2Signal` 从 pyta2 实例读取 `schema`、`output_keys`、`required_window` 和 `meta_info`。
- pyta2 当前不支持关闭输出缓存，适配时短期使用 `buffer_size=1`。

## 组合信号

组合信号应优先通过继承对应 data-kind 信号实现，而不是让用户手写复杂 graph 配置。K 线组合信号继承 `rKlineSignal`。

```python
class rTrendScore(rKlineSignal):
    name = "TrendScore"

    def __init__(self, **kwargs):
        self.macd = rPyta2Signal(
            name="macd",
            indicator_cls=rMACD,
            params={"n1": 26, "n2": 12, "n3": 9},
            input_map={"values": "closes"},
            return_dict=True,
        )
        self.atr = rPyta2Signal(
            name="atr",
            indicator_cls=rATR,
            params={"n": 14},
            input_map={"highs": "highs", "lows": "lows", "closes": "closes"},
            return_dict=True,
        )
        super().__init__(
            window=max(self.macd.required_window, self.atr.required_window),
            schema=[("score", Box(low=-float("inf"), high=float("inf")))],
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes):
        macd = self.macd.rolling(opens, highs, lows, closes, volumes)
        atr = self.atr.rolling(opens, highs, lows, closes, volumes)
        if atr["atr"] == 0:
            return float("nan")
        return macd["macd"] / atr["atr"]
```

后续可提供 `rCompositeSignal` 简化这类模板，但第一阶段不应为了组合能力过早暴露复杂 DSL。

## SignalEngine

`SignalEngine` 管理多个信号的实时和批量执行。

```python
engine = SignalEngine([
    SMA("close", window=10),
    ATR(window=14),
    rReturnSignal(n=5, name="ret5"),
])

row = engine.update(
    kline={
        "open": 101.0,
        "high": 103.0,
        "low": 100.0,
        "close": 102.0,
        "volume": 1200.0,
    }
)

matrix = engine.batch(kline_df)
```

如果 engine 中全部是 K 线信号，可以提供便捷形式：

```python
engine.update(open=101.0, high=103.0, low=100.0, close=102.0, volume=1200.0)
```

第一阶段行为：

- 每个信号拥有自己的 OHLCV buffer。
- `engine.update()` 按 data-kind 路由输入，再逐个调用信号的 `update()`。
- `engine.batch()` replay `update()`，不默认裁剪 warmup。
- 输出列按信号名和输出键稳定生成。

第二阶段优化：

- 引入共享 OHLCV buffer，减少重复存储。
- 引入 `SignalGraph`，支持跨信号依赖和拓扑排序。
- 引入 orderbook/trades data-kind 信号和对应输入路由。
- 引入声明式 `SignalSpec`，支持配置文件和批量生成。

## DSL 位置

DSL 应返回标准信号，而不是返回 pyta2 绑定声明。

```python
signals = [
    SMA("close", window=10),
    ATR(window=14),
    MACD("close", fast=12, slow=26, signal=9),
]
```

展开结果：

- `SMA("close", window=10)` 返回 `rPyta2Signal`，内部绑定 `values -> closes`。
- `ATR(window=14)` 返回 `rPyta2Signal`，内部绑定 `highs/lows/closes`。
- `MACD("close", ...)` 返回 `rPyta2Signal`，内部绑定 `values -> closes`。

## 与 FeatureSpec 的关系

`FeatureSpec` 不删除，但职责下调：

- 不作为第一公共 API。
- 后续可作为 `SignalSpec` 或矩阵输出声明。
- 用于序列化、网格搜索、自动生成大量信号。
- 不应迫使普通用户理解 pyta2 `forward()` 参数。

更合适的演进路径是：

```python
SignalSpec(name="sma10_close", signal=SMA("close", window=10))
```

而不是：

```python
FeatureSpec(cls=rSMA, bind={"values": "kline.close"})
```

## 查漏补缺

### 第一轮：是否仍然只是 pyta2 封装

不是。`rSignal` 是 sigma2 自有基类，自定义信号不依赖 pyta2 指标。pyta2 只是 `rPyta2Signal` 的输入来源之一。

### 第二轮：是否与 pyta2 结构一致

尽量一致。`window`、`schema`、`output_keys`、`required_window`、`rolling()`、`forward()`、`reset()`、`reset_extras()`、`outputs`、`g_index`、`return_dict`、`make_dict_output()`、`meta_info` 都应保留相同心智模型。主要差异是输入契约按 data-kind/family 标准化，单点 `update()` 只是 family 子类的补充接口。

### 第三轮：是否支持单点实时数据

支持。对 K 线，`rKlineSignal.update(open, high, low, close, volume)` 是 family 子类的一等单点输入接口，不是 batch 的附属能力。它追加内部 buffer 后委托 `rolling()`，从而复用 `rIndicator` 风格的 `g_index`、输出缓存和 `return_dict` 语义。其它 family 子类也应提供各自标准化的单点更新接口。

### 第四轮：是否过早泛化

不在第一阶段实现 orderbook/trades 的字段细节，但必须在基类层面留下 data-kind 扩展口。先把 `rSignal + rKlineSignal` 做稳，后续再扩展其它行情源。

## 新优先级

后续第一轮代码实现应按以下顺序：

1. 实现通用 `rSignal`，包含 schema 输出、`rolling()`、`reset()`、`meta_info` 和 family 元信息；`update()` 在 base 层最多作为 `rolling()` 兼容别名。
2. 实现 `rKlineSignal`，包含 OHLCV buffer、标准 K 线 rolling/update 输入。
3. 实现 1 到 2 个 K 线自定义信号测试，如 return、gap。
4. 实现 `rPyta2Signal`，把 rSMA、rATR、rMACD 适配为 K 线标准信号。
5. 实现最小 `SignalEngine.update()` 和 `SignalEngine.batch()`，内部按 data-kind 路由。
6. 再考虑 `SignalGraph`、共享 buffer、声明式 `SignalSpec`、orderbook/trades 和更多 DSL。
