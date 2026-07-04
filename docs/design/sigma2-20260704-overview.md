# sigma2 总体设计

更新时间：2026-07-04 16:35 CST

## 状态

本文是 `docs/design` 下唯一当前有效的总体设计文档。旧版阶段性设计已经移入 `docs/design/backup/`，仅保留历史追溯价值，不作为后续实现依据。

关键结论：

- sigma2 core 不是 `FeatureSet`。
- sigma2 core 是一套轻量、可继承、类似 `pyta2.base.rIndicator` 的 rolling signal 基类体系。
- `rSignal` 的概念、命名和生命周期应尽可能与 `rIndicator` 保持一致；只有输入 family 契约和单点 `update()` 是必要扩展。
- `FeatureSet`、DataFrame batch、ML 矩阵生成、minbt adapter 都是应用层能力，应该消费 core，而不是定义 core。
- 当前应优先冻结 `rSignal`、`rKlineSignal` 和 schema/output 契约，让用户立刻能写自定义信号并长期稳定使用。
- 上层 ML batch、DataFrame、minbt 等能力应围绕这套 core 继续扩展。

## 设计目标

sigma2 的最低稳定单元是“信号类”，而不是“特征集合”。

用户和二次开发者应该可以这样使用：

```python
from sigma2 import rKlineSignal, Space


class rGap(rKlineSignal):
    name = "gap"

    def __init__(self, **kwargs):
        super().__init__(
            window=2,
            schema=[("gap", Space.Scalar())],
            **kwargs,
        )

    @property
    def full_name(self):
        return "gap"

    def reset_extras(self):
        pass

    def forward(self, opens, highs, lows, closes, volumes):
        if len(closes) < 2:
            return float("nan")
        return opens[-1] / closes[-2] - 1.0


signal = rGap(return_dict=True)
row = signal.update(open=101.0, high=103.0, low=100.0, close=102.0, volume=1200.0)
```

这个信号类不依赖：

- `FeatureSet`
- pandas
- minbt
- pyta2 指标参数名
- 训练矩阵生成器
- 外部行情框架

这就是 sigma2 应该最先稳定的部分。

## 接口分层

| 层级 | 模块建议 | 稳定性 | 职责 |
| --- | --- | --- | --- |
| 核心层 | `sigma2.base` / `sigma2.core` | 最先稳定 | `rSignal`、family 子类、schema、输出、缓存、生命周期 |
| 内置信号层 | `sigma2.signals.*` | 随信号逐个稳定 | return、SMA、ATR、spread、VWAP 等信号类或构造器 |
| 适配层 | `sigma2.adapters.*` | 独立演进 | pyta2、minbt、其它框架的数据和指标适配 |
| 应用层 | `sigma2.app` / `sigma2.ml` | 后稳定 | `FeatureSet`、DataFrame batch、online state、训练矩阵 |

稳定性顺序：

1. 先稳定核心层。
2. 再稳定常用内置信号。
3. 再稳定 pyta2 adapter。
4. 最后稳定 `FeatureSet` 等应用层门面。

原因：应用层需求最容易随真实使用变化，核心信号继承契约一旦稳定，用户今天写的信号就能被未来任意应用层复用。

## 方案比较

### 方案 A：FeatureSet-first

```python
features = FeatureSet([kline.ret(5), kline.sma("close", 20)])
X = features.batch(df)
```

优点：

- 对普通 ML 用户很短。
- 容易连接 DataFrame、训练矩阵和回测。

缺点：

- 容易把 sigma2 做成应用框架。
- 自定义信号开发者必须理解上层编排。
- 未来 `FeatureSet` 调整会牵连核心信号使用方式。

结论：保留为应用层，不作为 core。

### 方案 B：SignalSpec-first

```python
SignalSpec(
    name="sma20",
    cls=rSMA,
    params={"n": 20},
    bind={"values": "close"},
)
```

优点：

- 声明式，适合配置文件、网格搜索和批量生成。
- 适合矩阵生成器消费。

缺点：

- 对手写信号不自然。
- 容易暴露 pyta2 的局部参数名。
- 容易让 sigma2 变成“绑定描述语言”而不是信号库。

结论：后续可作为序列化层，不作为 core。

### 方案 C：rSignal-first

```python
class rMySignal(rKlineSignal):
    def forward(self, opens, highs, lows, closes, volumes):
        ...
```

优点：

- 与 `pyta2.base.rIndicator` 心智一致。
- 用户继承一个类即可定义信号。
- 自定义信号、pyta2 适配信号、组合信号可以统一到同一个对象模型。
- 上层 `FeatureSet`、ML batch、minbt adapter 都能消费同一个信号对象。

缺点：

- DataFrame 一键训练矩阵不是 core 直接解决的问题。
- 需要额外应用层处理多信号编排和输出矩阵。

结论：采用，作为稳定核心。

### 方案 D：纯函数-first

```python
def gap(opens, highs, lows, closes, volumes):
    ...
```

优点：

- 最轻。
- 易测试。

缺点：

- 状态、缓存、schema、warmup、元信息都要额外约定。
- 无法自然表达 rolling online 生命周期。
- 与 pyta2 的 `rIndicator` 结构不一致。

结论：可作为内部实现辅助，不作为核心公共接口。

## 稳定核心对象

### rSignal

`rSignal` 是 sigma2 的核心公共开发接口。它应尽可能复刻 pyta2 的 `rIndicator` 心智模型。

必须保持一致的概念：

- `window`
- `schema`
- `buffer_size`
- `extra_window`
- `buffer_factor`
- `return_dict`
- `g_index`
- `rolling()`
- `forward()`
- `reset()`
- `reset_extras()`
- `full_name`
- `outputs`
- `output_keys`
- `required_window`
- `meta_info`
- `make_dict_output()`

sigma2 的必要差异只包含：

- 输入字段不在 `rSignal` 定义，而由 family 子类定义。
- family 子类可以提供单点 `update()`，但 `update()` 应委托到 `rolling()` 的生命周期，不重新发明输出和缓存语义。
- `rSignal` 增加 `family` 字段，用于表达输入类型驱动的信号族。

推荐伪接口：

```python
class rSignal:
    name: str | None = None
    family: str | None = None

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
        # base 层最多作为 rolling 的兼容别名；具体单点语义由 family 子类定义。
        ...

    def forward(self, *args, **kwargs):
        raise NotImplementedError

    def reset(self):
        ...

    def reset_extras(self):
        raise NotImplementedError

    def make_dict_output(self, output):
        ...

    @property
    def full_name(self):
        raise NotImplementedError

    @property
    def outputs(self):
        ...

    @property
    def output_keys(self):
        ...

    @property
    def required_window(self):
        ...

    @property
    def meta_info(self):
        ...
```

稳定字段：

- `window`
- `extra_window`
- `required_window`
- `schema`
- `output_keys`
- `outputs`
- `return_dict`
- `buffer_size`
- `buffer_factor`
- `name`
- `full_name`
- `family`
- `g_index`
- `meta_info`

兼容规则：

- 新增参数必须是 keyword-only 且有默认值。
- 不删除已公开属性。
- 不改变 `rolling()`、`forward()`、`reset()` 的核心生命周期语义。
- `rolling()` 是与 `rIndicator` 对齐的主生命周期入口。
- `update()` 在 base 层最多作为 `rolling()` 的兼容别名；在 family 子类中才表达单点行情输入，且必须复用 `rolling()` 的索引、缓存和返回语义。
- `meta_info` 可以新增字段，但不能删除已有字段。
- `make_dict_output()` 的输出 key 必须始终等于 `output_keys`。
- `return_dict` 默认值与 `rIndicator` 保持一致；应用层需要 dict 时显式传入 `return_dict=True`。

### family 子类

family 子类负责定义输入契约。`rSignal` 不直接知道 K 线、订单簿或成交字段。

设计关系：

```text
InputType / MarketDataKind -> SignalFamily -> rSignal subclass
```

公共字段统一使用 `family`。旧文档中的 `data_kind` 可作为内部兼容别名，但不应成为稳定公共命名。

## K 线核心：rKlineSignal

`rKlineSignal` 是第一批必须冻结的 family 子类。

```python
class rKlineSignal(rSignal):
    family = "kline"
    rolling_input_keys = ("opens", "highs", "lows", "closes", "volumes")
    update_input_keys = ("open", "high", "low", "close", "volume")

    def rolling(self, opens, highs, lows, closes, volumes):
        ...

    def update(self, open, high, low, close, volume):
        ...

    def forward(self, opens, highs, lows, closes, volumes):
        raise NotImplementedError
```

稳定语义：

- `rolling()` 接收窗口序列：`opens, highs, lows, closes, volumes`。
- `update()` 接收单个 K 线点：`open, high, low, close, volume`。
- `update()` 维护内部 OHLCV buffer，然后委托 `rolling(opens, highs, lows, closes, volumes)`。
- `rolling()` 继续负责推进 `g_index`、调用 `forward()`、写入 `outputs`、处理 `return_dict`。
- `forward()` 永远以标准 K 线序列为输入，不暴露 pyta2 的 `values` 等局部参数名。
- `open` 作为公共关键字保留；实现内部可用 `open_` 避免遮蔽内置函数。

这意味着用户今天继承 `rKlineSignal` 写出的信号，应能长期复用到：

- 手写实时策略
- `SignalEngine`
- `FeatureSet`
- minbt adapter
- ML batch runner

## 订单簿与成交扩展

orderbook/trade 现在要考虑扩展框架，但不应在没有足够真实信号前过度冻结 L2、L3、增量订单流等细节。

稳定原则：

- 新 family 必须通过新的 family 子类表达，而不是往 `rKlineSignal` 塞字段。
- 每个 family 子类必须定义自己的 `rolling_input_keys` 和 `update_input_keys`。
- 同一 family 下的信号必须共享同一套输入契约。
- 应用层只能根据 `family` 路由，不能写死外部框架名。

第一批候选输入契约：

```python
class rOrderBookSignal(rSignal):
    family = "orderbook"
    rolling_input_keys = ("bid_books", "ask_books")
    update_input_keys = ("bids", "asks")

    def rolling(self, bid_books, ask_books):
        ...

    def update(self, bids, asks):
        ...

    def forward(self, bid_books, ask_books):
        raise NotImplementedError
```

约定：

- `bids` / `asks` 是当前快照的档位序列，按最优价优先排序。
- 每个档位的最小形态是 `(price, size)`。
- `bid_books` / `ask_books` 是 rolling 窗口中的快照序列。

```python
class rTradeSignal(rSignal):
    family = "trade"
    rolling_input_keys = ("prices", "volumes", "sides")
    update_input_keys = ("price", "volume", "side")

    def rolling(self, prices, volumes, sides):
        ...

    def update(self, price, volume, side):
        ...

    def forward(self, prices, volumes, sides):
        raise NotImplementedError
```

约定：

- `side` 先采用 `"buy"` / `"sell"` / `None`。
- 更复杂的成交批次、逐笔 id、主动买卖识别可以通过子 family 或可选字段扩展，不能破坏上述最小契约。

冻结策略：

- `rKlineSignal` 在 v0.1 直接冻结。
- `rOrderBookSignal` 和 `rTradeSignal` 可在 v0.1 作为 experimental class 出现。
- 在各自至少有两个真实内置信号和 contract tests 后，再进入稳定承诺。

## 输出契约

schema 是稳定输出契约。

要求：

- 单输出信号可以返回标量。
- 多输出信号可以返回 tuple/list 或 mapping。
- `rSignal.make_dict_output()` 统一转换为 dict。
- dict key 必须等于 `output_keys`。
- `return_dict` 默认值与 `rIndicator` 保持一致；需要标准 dict 输出时显式设置 `return_dict=True`，或者由应用层调用 `make_dict_output()`。
- “标准化输出”指 schema、`output_keys` 和 `make_dict_output()` 契约稳定，不要求改变 `rIndicator` 的默认返回心智。

列名不是 core 的唯一职责，但 core 必须提供可稳定生成列名的信息：

```text
family
name
output_keys
full_name
```

应用层可以据此生成：

- `gap`
- `ret_5`
- `macd.dif`
- `kline.ret_5`

但不应要求 core 依赖 DataFrame。

## pyta2 关系

pyta2 是一个适配来源，不是 sigma2 core。

推荐：

```python
rPyta2Signal(
    name="sma_close_20",
    indicator_cls=rSMA,
    params={"n": 20},
    input_map={"values": "closes"},
)
```

稳定边界：

- `rPyta2Signal` 对外仍是 `rKlineSignal`。
- `input_map` 是 adapter 内部概念，不进入普通 K 线信号接口。
- sigma2 不重复维护 pyta2 指标定义，只读取其 `schema`、`output_keys`、`required_window`、`meta_info`。

## 应用层位置

`FeatureSet` 仍然有价值，但它不属于 core。

推荐位置：

```python
from sigma2.app import FeatureSet
```

职责：

- 管理多个 signal 实例。
- 做 batch replay 或向量化优化。
- 生成 DataFrame / numpy 矩阵。
- 处理 `DataSchema`。
- 管理多 symbol 对齐。
- 给 minbt adapter 或训练流程提供便利。

约束：

- `FeatureSet` 只能消费 `rSignal`，不能要求 signal 继承应用层类。
- `FeatureSet` 的变化不能破坏已存在的 `rKlineSignal` 自定义信号。
- minbt、backtrader、zipline 等名字不能出现在 core。

### FeatureSet 与 ML batch

`FeatureSet` 是应用层便利门面，用于把一组标准信号对象转成训练矩阵或在线特征行。

推荐形态：

```python
from sigma2.app import FeatureSet

features = FeatureSet([
    rReturn(n=1, name="ret_1", return_dict=True),
    rReturn(n=5, name="ret_5", return_dict=True),
    SMA("close", window=20, name="sma_close_20", return_dict=True),
])

X = features.batch(df, schema=schema)
state = features.online()
```

约束：

- `FeatureSet` 接收 `rSignal` 实例或能构造 `rSignal` 的声明。
- `FeatureSet.batch()` 可以 replay `rolling()` / `update()`，也可以后续向量化，但输出语义必须与 rolling replay 一致。
- `FeatureSet` 可以默认使用 `return_dict=True` 的信号实例，但不能改变 `rSignal` core 的默认心智模型。
- warmup 裁剪、标签对齐、样本过滤属于应用层策略，不能隐藏到 core。

### DataSchema

`DataSchema` 属于应用层数据标准化，不属于 core。

职责：

- 描述用户原始 DataFrame / dict / 框架数据到 family 输入字段的映射。
- 处理时间字段、symbol 字段和可用时间字段。
- 为 `FeatureSet.batch()`、adapter 和 online runner 构造 family 子类需要的标准输入。

示意：

```python
schema = DataSchema(
    time="dt",
    symbol="symbol",
    kline={
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    },
)
```

原则：

- 普通信号开发者不需要接触 `DataSchema`。
- `DataSchema` 不能反向影响 `rSignal` / `rKlineSignal` 的方法签名。

### FamilyRegistry

`FamilyRegistry` 是应用层和 runner 的扩展机制，不是 core 的父抽象。

用途：

- 根据 `family` 找到对应 family 子类、normalizer 和 runner。
- 让新增数据类型可以通过注册进入应用层，而不是修改 `FeatureSet` 的核心流程。

示意：

```python
registry.register_family(
    family="funding_rate",
    signal_base=rFundingRateSignal,
    normalizer=FundingRateNormalizer,
)
```

约束：

- 新增 family 的第一步是定义新的 `rSignal` family 子类。
- registry 只能组织和路由信号，不能改变信号类自身契约。
- `FeatureSet`、online state、adapter 可以依赖 registry；`rSignal` core 不依赖 registry。

### minbt adapter

minbt 是回测和交易执行框架，sigma2 是信号层。

边界：

- sigma2 core 不调用 broker。
- sigma2 core 不提交订单。
- minbt 的 `bar/bars` 命名只出现在 `sigma2.adapters.minbt`。
- adapter 只负责把 minbt 数据翻译为 sigma2 family 输入，并把信号输出交还策略。

推荐位置：

```python
from sigma2.adapters.minbt import MinbtFeatureAdapter
```

禁止：

- `rSignal`、`rKlineSignal`、`FeatureSet` core 流程中出现 `update_minbt_bars(...)`。
- 在 sigma2 core 中出现 `Broker`、下单、持仓、资金管理概念。

## 版本与兼容性

在 v0 阶段也要人为维持兼容规则。

推荐版本规划：

| 版本 | 冻结内容 |
| --- | --- |
| `0.1.x` | `rSignal`、`rKlineSignal`、schema/output、基础 K 线自定义信号 |
| `0.2.x` | pyta2 adapter、常用 K 线内置信号、最小 `SignalEngine` |
| `0.3.x` | `rOrderBookSignal`、`rTradeSignal` 的真实信号和 contract tests |
| `0.4.x` | `FeatureSet`、DataFrame batch、ML matrix builder |
| `1.0.0` | 对 core、常用内置信号和应用层主路径做正式语义化版本承诺 |

破坏性变更规则：

- core 破坏性变更必须进入下一个 minor，不能进入 patch。
- 已公开方法先 deprecate，不直接删除。
- 旧接口至少保留一个 minor 版本。
- 如果信号算法含义变化，必须改变 `name` / `full_name` 或在应用层声明 feature version，不能悄悄改变同名输出。

## Contract Tests

第一批实现必须用测试锁住稳定契约：

- 继承 `rKlineSignal` 的自定义信号可以只实现 `forward()` 和 `reset_extras()`。
- `update(open, high, low, close, volume)` 与手动 rolling replay 输出一致。
- `make_dict_output()` 对标量、tuple、mapping 的行为稳定。
- `output_keys` 与 dict 输出 key 完全一致。
- `required_window == window + extra_window`。
- `reset()` 清空状态和输出缓存。
- `meta_info` 包含稳定字段。
- `return_dict`、`g_index`、`outputs` 的行为与 `rIndicator` 保持同一心智模型。
- `rSignal` 不导入 pandas、minbt 或其它应用层依赖。

## 推荐实施顺序

1. 建立 Python 包骨架。
2. 实现 `sigma2.base.rSignal`、`Schema`、`Space` 或兼容包装。
3. 实现 `sigma2.families.kline.rKlineSignal`，并在顶层 re-export。
4. 实现 `rReturn`、`rGap` 两个纯 sigma2 K 线信号。
5. 写 core contract tests。
6. 实现 `rPyta2Signal`。
7. 实现最小 `SignalEngine`，仅作为 core 消费者，不反向污染 core。
8. 再实现 `FeatureSet`、DataFrame batch、minbt adapter。

最终判断：

```text
core-first:
    rSignal -> rKlineSignal -> concrete signals -> adapters/app

not app-first:
    FeatureSet -> hidden signal objects
```

这样 sigma2 可以立刻写、立刻用，并且未来高层接口变化不会破坏已经写好的信号类。
