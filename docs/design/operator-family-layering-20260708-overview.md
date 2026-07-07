# sigma2 算子层与数据 Family 层分层设计

更新时间：2026-07-08 06:25 CST

## 状态

本文是 `sigma2` 的专题设计文档，用于固定“pyta2-like 通用算子层”和“sigma2 数据 family 绑定层”的关系。

本文不替代 `docs/design/sigma2-20260704-overview.md`。总设计仍是项目级依据；本文只补充 signal / effect / target 在输入抽象上的分层逻辑。

核心结论：

- sigma2 需要正式区分两层：`primitive` 层和 `family binding` 层。
- `primitive` 层类似 pyta2：只关心最小必要输入，例如 `value`、`high`、`low`，不关心这些值来自 K 线、盘口还是成交。
- `family binding` 层属于 sigma2：按标准化数据类型分类，例如 `kline`、`orderbook`、`trade`，负责把市场事件字段绑定到 primitive 的输入。
- 用户主入口仍然是 `sigma2.kline.*`、`sigma2.orderbook.*`、`sigma2.trade.*` 等 family 目录。
- primitive 层是复用层和二次开发层，不应该反过来污染 sigma2 的按数据类型组织方式。
- signal 和 effect 都应该遵循这套分层。
- signal 的方向是正向 rolling：`step()` 推进状态，`forward()` 计算当前可用 feature。
- effect 的方向是反向 rolling：从序列末端向前回填，`backward()` 使用未来状态计算当前 anchor 的 target / outcome。
- `rEffect` 不应该暴露普通在线 `step()`；批量 target 生成由 `make_targets()` 或内部 runner 调用反向生命周期。
- 不强制用户理解 `KlineInput`、`OrderBookInput` 这类重对象；输入标准化和字段绑定由 family 层和 runner 负责。

## 背景问题

sigma2 当前总设计把 `rSignal` 定义为按输入数据类型分类的信号体系：

```text
kline      -> open / high / low / close / volume
orderbook  -> bids / asks
trade      -> price / volume / side
```

这对用户很直观，因为用户写 K 线信号时自然会进入 `sigma2.kline`，写盘口信号时自然会进入 `sigma2.orderbook`。

但很多真实信号和 target 并不需要完整 family 输入。

例如：

```text
SMA(close)                  只需要 value 序列
future_return(close, 5)     只需要 anchor close 和未来 close
future_ema(close, 20)       只需要反向的 value 状态
zscore(mid_price, 60)       只需要 value 序列
```

如果这些算子都写成：

```python
def forward(self, opens, highs, lows, closes, volumes):
    ...
```

会导致：

- 简单算子的签名冗余。
- 同一算子无法自然复用到 `close`、`open`、`vwap`、`mid_price`、`trade_price`。
- pyta2 适配层需要不断做重复字段绑定。
- effect / target 被迫接收完整 OHLCV，掩盖真正需要的未来字段。

反过来，如果只保留 pyta2-like 的泛化输入：

```python
def forward(self, values):
    ...
```

也会导致：

- sigma2 失去按数据输入类型定义 family 的核心结构。
- 用户必须自己理解字段绑定、事件标准化、数据来源。
- orderbook、trade、future funding、news 等非单序列输入被过度压扁。
- `make_features()`、`make_targets()` 难以稳定处理不同数据类型。

因此必须正式分层。

## 设计目标

本设计要同时满足两类开发者：

1. 普通使用者和策略研究者：按数据类型找到可用信号和 target。
2. 二次开发者和库维护者：复用通用计算逻辑，不重复实现 SMA、EMA、future return 等基础算子。

目标：

- 用户主入口短、直观。
- 二次开发时避免重复代码。
- 新增数据类型时只新增 family 和 binding，不修改已有 primitive。
- 新增通用算子时只新增 primitive，可以被多个 family 绑定。
- signal 和 effect 使用统一的分层模型。
- 未来机器学习训练路径中，输入 feature 和输出 target 都能被同一套 metadata 追踪。

非目标：

- 不把 sigma2 做成 pyta2 的全面迁移。
- 不把 primitive 层变成用户必须理解的主入口。
- 不在 core 中引入 `FeatureSet`、`ResearchDataset`、IC 分析或 minbt 语义。
- 不让 `bar/bars` 等外部框架词汇进入 sigma2 的核心命名。

## 两个正交维度

sigma2 的设计需要同时处理两个正交维度。

第一个维度是时间方向：

```text
Signal:
  历史 -> 当前
  正向 rolling
  生成 feature
  在线可用

Effect:
  未来 -> 当前 anchor
  反向 rolling
  生成 target / outcome
  只用于训练、评价、研究
```

第二个维度是输入抽象层级：

```text
Primitive:
  最小输入
  类似 pyta2
  例如 value / high / low
  可跨 family 复用

Family Binding:
  标准化市场数据输入
  例如 kline / orderbook / trade
  负责字段绑定和生命周期接入
```

组合后得到四类对象：

| 类型 | 时间方向 | 输入抽象 | 例子 |
| --- | --- | --- | --- |
| Signal primitive | 正向 | 最小输入 | `rValueSMA`、`rValueEMA` |
| Family signal | 正向 | 数据 family | `kline.rSMA(field="close")` |
| Effect primitive | 反向 | 最小输入 | `rValueForwardReturn`、`rValueFutureEMA` |
| Family effect | 反向 | 数据 family | `kline.rForwardReturn(field="close")`、`kline.rBoundTrigger` |

## 分层关系

推荐关系：

```text
用户 / research API
  |
  | make_features(data, signals=[...])
  | make_targets(data, effects=[...])
  v
family binding 层
  |
  | 标准化输入数据类型
  | 绑定字段
  | 维护正向或反向生命周期
  v
primitive 层
  |
  | 最小输入
  | 纯计算或轻状态 rolling
  v
schema / output
```

用户看到的是：

```python
from sigma2.kline import rSMA, rForwardReturn

signal = rSMA(20, field="close")
effect = rForwardReturn(5, field="close")
```

维护者可以复用：

```python
rSMA(field="close")       -> rValueSMA(value=close)
rSMA(field="open")        -> rValueSMA(value=open)
rOrderBookMidSMA(20)      -> rValueSMA(value=mid_price)
rForwardReturn("close")   -> rValueForwardReturn(value=close)
```

## Primitive 层

### 定位

primitive 层是 pyta2-like 的通用算子层。

特点：

- 输入名是局部语义，不是市场数据 schema。
- 只声明最小必要输入。
- 可以有状态。
- 可以被多个 family 绑定。
- 不负责标准化行情数据。
- 不负责 symbol、venue、time、DataFrame、minbt、训练集切分。

典型输入名：

```text
value
values
high
low
price
volume
unit
```

注意：

- `value` 不等于 `close`。
- `price` 不等于 K 线 close。
- primitive 不应该知道输入来自 kline、orderbook 还是 trade。

### Signal Primitive

Signal primitive 负责正向 rolling。

概念接口：

```python
class rSignalPrimitive:
    input_keys = ("value",)

    def forward(self, values):
        ...
```

例子：

```python
class rValueSMA(rSignalPrimitive):
    input_keys = ("value",)

    def __init__(self, n):
        self.n = n

    def forward(self, values):
        return values[-self.n:].mean()
```

这里的 `values` 是 primitive 局部输入，不是 K 线 close 的固定名字。

### Effect Primitive

Effect primitive 负责反向 rolling。

概念接口：

```python
class rEffectPrimitive:
    anchor_keys = ("value",)
    future_keys = ("value",)

    def backward(self, value):
        ...
```

关键不变量：

- `backward()` 计算当前 anchor 的 target / outcome。
- 调用 `backward()` 时，future state 已经包含当前 anchor 之后的数据。
- future state 不包含当前 anchor。
- `backward()` 完成后，runner 再把当前 anchor 放入 future state，供更早的样本使用。

例子：

```python
class rValueForwardReturn(rEffectPrimitive):
    anchor_keys = ("value",)
    future_keys = ("value",)

    def __init__(self, horizon):
        self.horizon = horizon

    def backward(self, value):
        if len(self.future["value"]) < self.horizon:
            return float("nan")
        future_value = self.future["value"][self.horizon - 1]
        return future_value / value - 1.0
```

逆向 EMA 例子：

```python
class rValueFutureEMA(rEffectPrimitive):
    anchor_keys = ("value",)
    future_keys = ("value",)

    def __init__(self, n):
        self.alpha = 2.0 / (n + 1)
        self._ema = None

    def reset_extras(self):
        self._ema = None

    def backward(self, value):
        if len(self.future["value"]) == 0:
            return float("nan")

        next_value = self.future["value"][0]
        if self._ema is None:
            self._ema = next_value
        else:
            self._ema = self.alpha * next_value + (1.0 - self.alpha) * self._ema
        return self._ema
```

这类 effect 不能自然表达成正向 `forward()`，因为它的状态天然从序列末端向前递推。

## Family Binding 层

### 定位

family binding 层是 sigma2 的用户主入口。

特点：

- 按输入数据类型分类。
- 暴露稳定的标准化输入契约。
- 负责把 family 字段绑定到 primitive 输入。
- 负责生命周期接入。
- 负责输出 schema、full name、metadata。
- 可以包装 primitive，也可以直接实现 family-specific 逻辑。

典型 family：

```text
kline
orderbook
trade
funding_rate
news
```

### Kline Signal Binding

K 线标准输入仍是：

```text
open
high
low
close
volume
```

通用字段信号可以通过 `field` 绑定 primitive：

```python
class rSMA(rKlineFieldSignal):
    def __init__(self, n, field="close", **kwargs):
        super().__init__(
            primitive=rValueSMA(n),
            bind={"value": field},
            **kwargs,
        )
```

用户使用：

```python
signal = rSMA(20, field="close")
```

对于用户而言，这是一个 K 线信号，不是裸 pyta2 算子。

### Kline Effect Binding

K 线 target 可以通过 `field` 绑定 effect primitive：

```python
class rForwardReturn(rKlineFieldEffect):
    def __init__(self, horizon, field="close", **kwargs):
        super().__init__(
            primitive=rValueForwardReturn(horizon),
            bind={"value": field},
            **kwargs,
        )
```

用户使用：

```python
effect = rForwardReturn(5, field="close")
```

生成训练标签：

```python
targets = make_targets(
    data=klines,
    effects=[
        rForwardReturn(5, field="close"),
    ],
)
```

### Family-specific Signal / Effect

不是所有对象都应该拆成 primitive。

例如 K 线止盈止损触发：

```python
class rBoundTrigger(rKlineEffect):
    ...
```

它依赖 K 线内部路径假设：

```text
open -> high -> low -> close
open -> low -> high -> close
```

这种逻辑是 family-specific，不应该假装成通用 `value` primitive。

判断标准：

- 如果计算逻辑只依赖抽象序列值，应进入 primitive。
- 如果计算逻辑依赖 family 的数据结构、事件顺序或市场假设，应留在 family 层。

## Signal 生命周期

signal 负责生成模型输入 feature。

生命周期：

```text
reset()
for row in data from left to right:
    signal.step(row)
      -> 更新当前/历史状态
      -> forward(...)
      -> 写入输出缓存
```

不变量：

- `step()` 是用户和 runner 的唯一在线推进入口。
- `forward()` 是子类计算 hook。
- `forward()` 不推进 core 生命周期。
- signal 只能使用当前和历史可用数据。
- signal 输出进入 `FeatureData`。

示意：

```text
t0 -> t1 -> t2 -> t3
      history + current -> feature[t]
```

## Effect 生命周期

effect 负责生成训练输出 target / outcome。

生命周期：

```text
reset()
for row in data from right to left:
    effect.step_back(row)
      -> backward(...) 使用已积累的 future state
      -> 写入 target 输出
      -> 把当前 row 纳入 future state
```

`step_back()` 是内部 runner 名称，不建议作为普通用户 API。

不变量：

- `backward()` 是 effect 作者实现的计算 hook。
- `backward()` 使用当前 anchor 和当前 anchor 之后的 future state。
- future state 不包含当前 anchor。
- `backward()` 完成后才把当前 anchor 加入 future state。
- effect 输出进入 `TargetData`。
- effect 不应该被在线策略当作 feature 使用。

示意：

```text
t0 <- t1 <- t2 <- t3
future[t] = rows after t
anchor + future -> target[t]
```

以 `horizon=2` 为例：

```text
处理 t3: future = []        -> target[t3] = NaN
处理 t2: future = [t3]      -> target[t2] = NaN
处理 t1: future = [t2,t3]   -> target[t1] 可计算
处理 t0: future = [t1,t2]   -> target[t0] 可计算
```

## 命名规范

推荐命名：

```text
rSignal              core 正向信号基类
rKlineSignal         K 线 signal family 基类
rKlineWindowSignal   显式维护 K 线历史窗口的 signal 基类

rEffect              core 反向 effect 基类
rKlineEffect         K 线 effect family 基类
rKlineFieldEffect    绑定单字段 primitive 的 K 线 effect 基类

rSignalPrimitive     正向通用算子基类
rEffectPrimitive     反向通用 outcome 算子基类
```

命名原则：

- 用户常用类仍使用 `rXxx`，保持和 `pyta2.base.rIndicator` 的 rolling 类心智一致。
- signal 的 hook 叫 `forward()`。
- effect 的 hook 叫 `backward()`。
- 普通用户不需要直接调用 `backward()`。
- `outcome` 是文档中的业务概念，不作为核心 hook 名。
- `target` 是批量数据对象概念，例如 `TargetData`。
- `effect` 是生成 target / outcome 的算子概念。

## 推荐源码组织

保持总设计中“根目录优先是信号输入类型分类”的原则。

推荐第一阶段结构：

```text
sigma2/
  core/
    signal.py
    effect.py
    primitive.py
    kline.py
    orderbook.py
    trade.py
  kline/
    sma.py
    return_.py
    forward_return.py
    bound_trigger.py
  orderbook/
    book_spread.py
    mid_sma.py
  trade/
    trade_signed_volume.py
  utils/
    pyta2.py
```

说明：

- `core/primitive.py` 放最小 primitive 基类和少量基础组合能力。
- 具体用户可发现对象仍放在 `kline/`、`orderbook/`、`trade/`。
- 第一阶段不新增根级 `ops/` 或 `primitives/` 目录，避免破坏“根目录就是数据类型分类”的结构。
- 如果未来 primitive catalogue 变大，可以在评审后引入 `core/primitives/` 子目录，但不改变用户主入口。
- 每个 family 具体信号或 effect 仍建议一个文件。

## 用户接口

普通用户不需要知道 primitive。

生成 feature：

```python
from sigma2.kline import rSMA, rReturn

features = make_features(
    data=klines,
    signals=[
        rSMA(20, field="close"),
        rReturn(5),
    ],
)
```

生成 target：

```python
from sigma2.kline import rForwardReturn

targets = make_targets(
    data=klines,
    effects=[
        rForwardReturn(5, field="close"),
    ],
)
```

深度学习训练：

```python
dataset = make_dataset(
    features=features,
    targets=targets,
)

X, y = dataset.train.to_sequence(lookback=60)
```

这些接口中不出现：

- `KlineInput`
- `Primitive`
- `step_back`
- `backward`
- `pyta2` 参数绑定细节

## 二次开发接口

### 新增通用 signal primitive

适用于可跨 family 复用的正向算子。

```python
class rValueZScore(rSignalPrimitive):
    input_keys = ("value",)

    def __init__(self, n):
        self.n = n

    def forward(self, values):
        ...
```

然后由 family 绑定：

```python
class rZScore(rKlineFieldSignal):
    def __init__(self, n, field="close", **kwargs):
        super().__init__(
            primitive=rValueZScore(n),
            bind={"value": field},
            **kwargs,
        )
```

### 新增通用 effect primitive

适用于可跨 family 复用的反向 outcome 算子。

```python
class rValueFutureMaxReturn(rEffectPrimitive):
    anchor_keys = ("value",)
    future_keys = ("value",)

    def __init__(self, horizon):
        self.horizon = horizon

    def backward(self, value):
        if len(self.future["value"]) < self.horizon:
            return float("nan")
        future_max = max(self.future["value"][: self.horizon])
        return future_max / value - 1.0
```

然后由 family 绑定：

```python
class rFutureMaxReturn(rKlineFieldEffect):
    def __init__(self, horizon, field="close", **kwargs):
        super().__init__(
            primitive=rValueFutureMaxReturn(horizon),
            bind={"value": field},
            **kwargs,
        )
```

### 新增 family-specific effect

适用于依赖 family 结构的 target / outcome。

```python
class rBoundTrigger(rKlineEffect):
    required_keys = ("open", "high", "low", "close", "atr")

    def backward(self, open, high, low, close, atr):
        ...
```

这种类不需要经过 primitive。

## Binding 契约

binding 的职责是把 family 字段映射到 primitive 局部输入。

例子：

```python
bind = {"value": "close"}
```

含义：

```text
primitive input "value"  <-  kline field "close"
```

更复杂的例子：

```python
bind = {
    "high": "high",
    "low": "low",
    "value": "close",
}
```

约束：

- primitive 声明的所有 `input_keys`、`anchor_keys`、`future_keys` 都必须能通过 binding 得到。
- binding 右侧必须是 family 已知字段或 family 提供的派生字段。
- 缺失字段必须报错，不能静默返回 NaN。
- 同一个 primitive 可以被不同 family 绑定。
- metadata 必须记录 binding，以保证实验可复现。

推荐 metadata：

```text
family
signal_or_effect_name
primitive_name
bind
params
schema
output_keys
direction: forward | backward
```

## 派生字段

family 层可以提供派生字段。

例如 orderbook：

```text
mid_price = (best_bid + best_ask) / 2
spread = best_ask - best_bid
imbalance = bid_size / (bid_size + ask_size)
```

然后通用 primitive 可以绑定：

```python
rSMA(20, field="mid_price")
```

约束：

- 派生字段必须由 family 明确定义。
- 派生字段的可用时间必须继承或显式声明。
- 派生字段不能偷偷使用未来数据。
- 派生字段应进入 metadata。

## Effect 与 TargetData

`rEffect` 是算子。

`TargetData` 是批量计算结果。

关系：

```text
rEffect.backward(...)  ->  每个 anchor 的 outcome
make_targets(...)      ->  批量执行反向 runner
TargetData             ->  保存 target values / mask / metadata
```

`TargetData` 至少应记录：

```text
time
symbol
values
columns
mask
target_start_time
target_end_time
effect metadata
```

其中 effect metadata 应包含：

```text
effect full_name
family
primitive
bind
horizon
schema
direction = backward
```

## 与 pyta2 的关系

pyta2 的核心价值是通用 rolling indicator。

sigma2 的目标不是全面复制 pyta2，而是：

- 复用 pyta2 已有 indicator。
- 保持和 `pyta2.base.rIndicator` 相近的轻量类心智。
- 在 sigma2 中增加数据 family 绑定和标准化输入输出。
- 在 effect / target 方向上借鉴 fintools 的反向 rolling 思路。

关系：

```text
pyta2 indicator
  -> sigma2 primitive 或 pyta2 adapter
  -> sigma2 family signal
  -> FeatureData
```

未来 pyta2 暴露 `rSMA` 等类后，sigma2 可以通过 adapter 把它们绑定到 K 线字段：

```python
rPyta2SMA(20, field="close")
```

这仍然属于 family signal，而不是把 pyta2 目录变成 sigma2 的主结构。

## 与 research 层的关系

research 层消费 family 层对象，而不是直接依赖 primitive。

推荐：

```text
make_features(data, signals=[family signal])
make_targets(data, effects=[family effect])
```

research runner 可以识别 primitive metadata，但不应该要求普通用户传 primitive。

优点：

- 用户接口稳定。
- 训练集生成器不用理解每个 primitive 的内部细节。
- metadata 足够追踪复现实验。
- 新增 family 不需要修改 research 主接口。

## 方案比较

### 方案 A：所有信号都固定 family 全量输入

例子：

```python
def forward(self, opens, highs, lows, closes, volumes):
    ...
```

优点：

- K 线语义直接。
- family 边界清晰。

缺点：

- 简单算子冗余。
- 复用差。
- `SMA(close)`、`SMA(open)`、`SMA(mid_price)` 会重复实现。
- effect target 会被迫接收不必要字段。

结论：不采用为唯一模型。

### 方案 B：所有信号都使用 pyta2-like 最小输入

例子：

```python
def forward(self, values):
    ...
```

优点：

- 复用强。
- 适合数学算子。

缺点：

- 用户失去按数据类型理解信号的入口。
- orderbook/trade 等复杂输入难以自然表达。
- 字段绑定和时间可用性容易散落到应用层。

结论：不采用为唯一模型。

### 方案 C：primitive + family binding 双层

例子：

```python
rValueSMA(value)
rSMA(field="close")
```

优点：

- 用户接口保持 family 化。
- 二次开发复用 primitive。
- signal 和 effect 都能统一建模。
- 新数据类型扩展只需新增 family binding。
- 通用算法和市场数据语义分离。

缺点：

- 比单层模型多一个内部概念。
- 需要明确 metadata 和 binding contract。
- 第一阶段需要控制 primitive 层规模，避免过早变成第二套 pyta2。

结论：采用。

## Contract Tests

分层设计需要用 contract tests 锁定。

Signal 侧：

- `rSignal.step()` 是正向在线入口。
- `rSignal.forward()` 不推进生命周期。
- `rKlineFieldSignal` 只把声明字段绑定给 primitive。
- primitive 缺少输入字段时必须报错。
- 同一 primitive 绑定不同字段时 full name 和 metadata 必须不同。
- signal metadata 必须记录 `family`、`primitive`、`bind`。

Effect 侧：

- `rEffect` 不暴露普通在线 `step()`。
- 反向 runner 从序列末尾向前执行。
- `backward()` 调用时 future state 不包含当前 anchor。
- `backward()` 完成后当前 anchor 才进入 future state。
- `horizon` 不足时返回缺失，并设置 mask。
- effect metadata 必须记录 `direction="backward"`。
- `TargetData` 中必须保留 `target_start_time` 和 `target_end_time`。
- effect 不得进入 `FeatureData`，除非用户显式构造泄漏测试场景。

Binding 侧：

- binding 右侧字段不存在时必须报错。
- 派生字段必须有明确来源和可用时间。
- 多 family 绑定不传对齐策略时必须报错。
- metadata 必须足以复现实验。

## 第一阶段实施建议

第一阶段只做最小闭环，不做完整 catalog。

建议顺序：

1. 在设计上确认 `rSignal.forward()` 与 `rEffect.backward()` 的方向约定。
2. 定义最小 `rEffect` 基类和反向 runner，不先暴露复杂公共 API。
3. 定义 `rSignalPrimitive`、`rEffectPrimitive` 或等价的最小 primitive 契约。
4. 实现一个 `rKlineFieldSignal`，用 `rValueSMA` 验证 signal binding。
5. 实现一个 `rKlineFieldEffect`，用 `rValueForwardReturn` 验证 target binding。
6. 实现一个 family-specific `rBoundTrigger`，验证不是所有 effect 都必须 primitive 化。
7. 在 research 层通过 `make_features()`、`make_targets()` 消费 family 对象。
8. 用 contract tests 锁定方向、binding、metadata、mask。

暂不优先做：

- 全面迁移 pyta2 指标。
- 完整 primitive catalogue。
- 复杂 DAG。
- 多进程分布式计算。
- minbt 深度集成。
- gymnasium 兼容层。

## 最终判断

sigma2 的核心结构应该是：

```text
按数据类型组织用户入口
按最小输入复用计算逻辑
```

也就是：

```text
family 是用户心智模型
primitive 是二次开发复用模型
```

signal 和 effect 分别对应两个时间方向：

```text
rSignal.forward()   正向生成 feature
rEffect.backward()  反向生成 target / outcome
```

这套设计同时保留了：

- pyta2 的轻量 rolling 算子心智。
- sigma2 的标准化数据 family 结构。
- ML 训练中输入 feature 和输出 target 的严格隔离。
- 未来扩展 orderbook、trade、funding、news 等数据类型的空间。
