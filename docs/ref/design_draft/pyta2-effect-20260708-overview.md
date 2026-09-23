# pyta2.effect 反向滚动结果算子设计

更新时间：2026-07-08 06:58 CST

## 状态

本文是 `pyta2.effect` 的专题设计文档，用于规划如何把 `fintools/spaces/frozen/effect/_effect` 中的数据无关 effect 算子整理并迁移到 pyta2。

本文只讨论 pyta2 层，不讨论 sigma2 的具体 family binding 实现。

核心结论：

- pyta2 是第一层通用 rolling 算子库。
- sigma2 是第二层按数据输入类型分类的绑定层。
- `rIndicator` 负责正向 rolling，生成当前可用的 indicator / feature。
- 新增 `rEffect` 负责反向 rolling，生成当前 anchor 的未来结果 target / outcome。
- `rEffect` 应放在 `pyta2.base.effect`，并与 `rIndicator` 保持尽可能一致的轻量类心智。
- `pyta2.effect` 只放与 `kline`、`orderbook`、`trade` 无关的通用 effect。
- `ATR` 等金融字段名不应进入通用 effect 命名；应抽象为 `unit`。
- K 线、盘口、成交等字段绑定由 sigma2 完成，不进入 pyta2。
- `fintools` 中的 `reXXX` 类可作为语义来源，但不直接照搬命名和结构。
- 第一阶段目标是形成 `rEffect`、`backward_rolling_apply()`、`rFutureReturn`、`rFutureSMA`、`rFutureEMA`、`rBoundTrigger` 的最小闭环。

## 背景

pyta2 当前已经有稳定的正向 rolling 抽象：

```text
rIndicator
  rolling(...)
    -> forward(...)
```

它适合表达：

```text
历史窗口 + 当前点 -> 当前 indicator / feature
```

但监督学习、因子研究和策略评价还需要另一类对象：

```text
当前 anchor + 未来路径 -> 当前样本的 target / outcome
```

例如：

```text
未来 5 步收益
未来 20 步最大上涨
未来 20 步最大回撤
未来窗口均值
未来窗口波动率
未来触发上界或下界
未来追踪止损触发结果
```

这些对象不是在线 feature，不能由正向 `rIndicator.forward()` 表达。它们需要从序列末端向前运行，因为每个过去点的结果依赖它右侧的未来数据。

`fintools/spaces/frozen/effect/_effect` 已经有一批类似对象，例如：

```text
reChg
reRoChg
reSMA
reEMA
reMax
reMin
reKthTop
reBoundTrigger
reTrailingTrigger
```

这些内容应被整理成 pyta2 的通用 effect 层，供 sigma2 后续按数据 family 绑定使用。

## 分层边界

最终边界：

```text
pyta2:
  通用 rolling 算子
  不知道 kline / orderbook / trade
  输入是 values / highs / lows / units 等最小必要序列

sigma2:
  标准化市场数据 family
  负责把 close / mid_price / trade_price 等字段绑定到 pyta2 算子
  负责 FeatureData / TargetData / make_features / make_targets
```

示例：

```text
pyta2.effect.rFutureReturn(values, horizon=5)

sigma2.kline.rForwardReturn(horizon=5, field="close")
sigma2.orderbook.rForwardReturn(horizon=5, field="mid_price")
sigma2.trade.rForwardReturn(horizon=5, field="price")
```

因此 pyta2 不应出现：

```text
kline
orderbook
trade
open/high/low/close 固定事件对象
TargetData
IC 分析
ResearchDataset
minbt
```

pyta2 可以出现：

```text
values
prices
highs
lows
opens
closes
units
future return
future stats
path trigger
```

其中 `opens/highs/lows/closes` 只表示路径算法需要的通用 OHLC 路径压缩格式，不表示 sigma2 的 K 线 family。

## rIndicator 与 rEffect

`rIndicator` 和 `rEffect` 是平行概念。

| 对象 | 时间方向 | 状态入口 | 计算 hook | 用途 |
| --- | --- | --- | --- | --- |
| `rIndicator` | 从左到右 | `rolling()` | `forward()` | 当前可用 feature |
| `rEffect` | 从右到左 | `rolling()` | `backward()` | 未来 target / outcome |

保留 `rolling()` 作为状态入口的原因：

- 与 pyta2 现有 `rIndicator` 心智一致。
- `rolling()` 表示“由 runner 按某个方向推进状态”，不是特指时间正向。
- 方向由对象类型和 runner 决定：`rIndicator` 用 `forward_rolling_apply()`，`rEffect` 用 `backward_rolling_apply()`。

`backward()` 是 effect 作者实现的 hook。普通 sigma2 / ML 用户不会直接调用它。

## rEffect 基类

推荐新增：

```text
pyta2/base/effect.py
```

概念接口：

```python
class rEffect:
    name = None
    direction = "backward"

    def __init__(
        self,
        window,
        schema,
        *,
        buffer_size=1,
        extra_window=0,
        buffer_factor=2,
        return_dict=False,
    ):
        ...

    def rolling(self, *args, **kwargs):
        self.g_index += 1
        output = self.backward(*args, **kwargs)
        ...
        return output

    def reset(self):
        ...

    def reset_extras(self):
        ...

    def backward(self, *args, **kwargs):
        ...

    @property
    def full_name(self):
        ...
```

应与 `rIndicator` 保持一致的属性：

```text
name
window
schema
output_keys
outputs
required_window
g_index
return_dict
make_dict_output()
meta_info
reset()
reset_extras()
```

新增或明确的属性：

```text
direction = "backward"
horizon: 可选，由具体 effect 定义
```

`meta_info` 推荐包含：

```text
name
full_name
direction
schema
window
extra_window
required_window
buffer_size
buffer_factor
return_dict
g_index
```

输出缓存契约：`buffer_size > 0` 保留最近 N 条，`buffer_size=0` 或 `None` 关闭缓存，`buffer_size=-1` 表示无限缓存；小于 `-1` 的值非法。默认值为 `1`。

### outputs 顺序

`rEffect.rolling()` 的调用方向是从右向左，因此 `rEffect.outputs` 如果按 `rolling()` 调用时追加，内部顺序是反向调用顺序，不是原始时间正序。

第一阶段约定：

- `backward_rolling_apply()` 的返回值是稳定公共结果，必须恢复为原始时间正序。
- `rEffect.outputs` 只表示当前 effect 实例的调用顺序缓存，不承诺是时间正序结果表。
- 普通批量用户不应依赖 `obj.outputs` 获取最终 target；应使用 `backward_rolling_apply()` 的返回值。
- 如果未来要让 `rEffect.outputs` 支持时间正序，必须作为单独设计修改，不能隐式改变语义。

## 反向滚动语义

`rEffect` 的核心不变量：

```text
输入序列 values 以当前 anchor 开头
values[0]  是当前 anchor
values[1:] 是当前 anchor 之后的未来数据
window     通常等于 horizon + 1
```

批量 runner 从右向左执行：

```text
原始时间: t0, t1, t2, t3, t4

执行顺序:
  t4 -> t3 -> t2 -> t1 -> t0
```

在第 `i` 次调用中：

```text
values = original_values[i:]
```

输出最终再恢复为原始时间正序。

以 `horizon=2` 为例：

```text
t4: future 不足 -> NaN
t3: future 只有 t4 -> NaN
t2: 可看到 t3,t4 -> target[t2]
t1: 可看到 t2,t3 -> target[t1]
t0: 可看到 t1,t2 -> target[t0]
```

## backward_rolling_apply

推荐在 `pyta2.base.utils` 增加：

```python
def backward_rolling_apply(
    num,
    obj_cls,
    param_args=None,
    param_kwargs=None,
    input_args=None,
    input_kwargs=None,
    doroll_input_args=None,
    doroll_input_kwargs=None,
    return_type="tuple",
    return_meta_info=False,
):
    ...
```

与 `forward_rolling_apply()` 保持参数风格一致。

执行规则：

```python
output_table = VectorTable(capacity=num)
obj = obj_cls(..., return_dict=True)

for i in range(num - 1, -1, -1):
    end = min(i + obj.required_window, num)
    sliced_args = [arg[i:end] if should_roll else arg for arg in input_args]
    sliced_kwargs = {key: val[i:end] if should_roll else val for key, val in input_kwargs.items()}
    output = obj.rolling(*sliced_args, **sliced_kwargs)
    output_table.append(output)

return get_outputs(output_table, return_type=return_type, reverse=True)
```

注意：

- `obj` 在整个反向循环中保持同一个实例。
- 这允许 `rFutureEMA` 这类对象从未来末端向过去递推状态。
- 不应每个 anchor 新建一个对象，否则会破坏反向状态型 effect。
- 输出顺序默认恢复为原始时间正序。
- 固定 `n_forward` 的 effect 默认只切片 `i:i+required_window`，避免把完整后缀 `i:` 传入每个 anchor 导致不必要的 O(N^2) 风险。
- `n_forward=None` 只用于原始 `fintools` 已支持的 effect，例如 trigger；runner 对这类对象传入 `i:` 后缀。

## 命名规则

### 类名前缀

pyta2 现有 rolling 类使用 `r` 前缀，但 effect primitive 从 `fintools` 迁移时应优先保留原始 `re*` 语义和参数命名：

```text
reRoChg
reEMA
reMax
reBoundTrigger
```

pyta2 可以提供 `rFuture*` 兼容导入路径，但不应让这些别名引入第二套计算语义：

```python
rFutureReturn = reRoChg
rFutureEMA = reEMA
```

primitive 层的稳定语义来自 `fintools` 源文件；sigma2 负责在 family 层提供更贴近 K 线、orderbook、trades 的用户接口。

### 方法命名

采用：

```text
rIndicator.forward()
rEffect.backward()
```

原因：

- `forward()` 表示从历史到当前。
- `backward()` 表示从未来向当前 anchor 回填结果。
- 与 `fintools` 的 effect 心智一致。
- `backward()` 不作为 ML 用户主入口，只作为 pyta2 effect 作者的 hook。

### 输出字段命名

primitive 层输出字段优先遵守 `fintools` 原始实现。

推荐：

```text
change
pct_change
atr_change
value
trigger
profit
trigger_price
trigger_location
trigger_ref_price
trigger_ref_location
```

family 包装层可以重新映射为更适合用户/训练数据的字段名，例如：

```text
return
unit_change
trigger_index
```

但这属于 sigma2 等上层包的职责，不应改变 pyta2 primitive 的原始 schema。

## 模块结构

推荐新增：

```text
pyta2/
  base/
    effect.py
  effect/
    __init__.py
    change.py
    ma.py
    stats.py
    rank.py
    path.py
    trigger.py
    _batch.py
```

模块职责：

```text
change.py:
  rFutureChange
  rFutureReturn
  rFutureUnitChange

ma.py:
  rFutureSMA
  rFutureEMA
  rFutureWMA

stats.py:
  rFutureMax
  rFutureMin
  rFutureMean
  rFutureStd
  rFutureMedian

rank.py:
  rFutureKthTop
  rFutureKthBottom

path.py:
  rFutureHighChange
  rFutureLowChange
  rFutureHighLowUnitChange

trigger.py:
  rBoundTrigger
  rTrailingTrigger

_batch.py:
  eFutureReturn(...)
  eFutureMax(...)
  等可选快捷函数
```

`_batch.py` 不是第一阶段必须项。第一阶段可以先让用户直接使用 `backward_rolling_apply()`。

## 从 fintools 的迁移映射

### change.py

| fintools | pyta2 | 说明 |
| --- | --- | --- |
| `reChg` | `rFutureChange` | `values[n_forward] - values[0]` |
| `reRoChg` | `rFutureReturn` | `values[n_forward] / values[0] - 1` |
| `reATRoChg` | `rFutureUnitChange` | `(values[n_forward] - values[0]) / units[0]` |
| `reSMAChg` | `rFutureSMAChange` | 未来 SMA 相对 anchor 的变化，可第二阶段 |
| `reRoSMAChg` | `rFutureSMAReturn` | 未来 SMA 收益，可第二阶段 |
| `reATRoSMAChg` | `rFutureSMAUnitChange` | 未来 SMA unit 变化，可第二阶段 |

这些组合类应按 `fintools/_effect/change.py` 原始逻辑迁移，不应重新设计公式或输出键。

```text
rFutureChange
rFutureReturn
rFutureUnitChange
```

`SMAChange`、`EMAChange` 等组合类可以通过 `rFutureSMA` 与 change 类组合实现，后续再决定是否提供快捷类。

### ma.py

| fintools | pyta2 | 说明 |
| --- | --- | --- |
| `reSMA` | `rFutureSMA` | `mean(values[1:n_forward+1])` |
| `reEMA` | `rFutureEMA` | 反向 EMA，单实例从右向左递推 |
| `reWMA` | `rFutureWMA` | 未来窗口加权均值 |

`rFutureEMA` 是必须支持反向有状态 rolling 的关键测试对象。

推荐定义：

```text
ema[t] = alpha * values[t+1] + (1 - alpha) * ema[t+1]
alpha = 2 / (n + 1)
```

当前实现按 `fintools` 原始逻辑：

- 首次有效调用时使用 `mean(values[1:n_forward+1])` 初始化 `_ema`。
- 随后用 `values[1]` 递推 `_ema`。
- runner 必须从右向左复用同一个实例，否则会破坏原始反向 EMA 语义。

### stats.py

| fintools | pyta2 | 说明 |
| --- | --- | --- |
| `reMax` | `rFutureMax` | 未来窗口最大值 |
| `reMin` | `rFutureMin` | 未来窗口最小值 |
| `reMean` | `rFutureMean` | 未来窗口均值 |
| `reStd` | `rFutureStd` | 未来窗口标准差 |
| `reMedian` | `rFutureMedian` | 未来窗口中位数 |

这些类输出 key 统一用：

```text
value
```

如需表达相对 anchor 的变化，应使用 `path.py` 或 change 组合类。

### rank.py

| fintools | pyta2 | 说明 |
| --- | --- | --- |
| `reKthTop` | `rFutureKthTop` | 未来窗口第 k 大 |
| `reKthBottom` | `rFutureKthBottom` | 未来窗口第 k 小 |
| `reKthTopChg` | `rFutureKthTopChange` | 第二阶段可选 |
| `reKthBottomChg` | `rFutureKthBottomChange` | 第二阶段可选 |

第二阶段再迁移：

```text
rFutureKthTop
rFutureKthBottom
```

### path.py

| fintools | pyta2 | 说明 |
| --- | --- | --- |
| `reHigh` | `rFutureHigh` | 可作为 `rFutureMax` 别名或不迁移 |
| `reLow` | `rFutureLow` | 可作为 `rFutureMin` 别名或不迁移 |
| `reHighChg` | `rFutureHighChange` | `max(highs[1:n_forward+1]) - price[0]` |
| `reLowChg` | `rFutureLowChange` | `min(lows[1:n_forward+1]) - price[0]` |
| `reATRoHighLowChg` | `rFutureHighLowUnitChange` | 输出 high/low 的 unit 变化 |

推荐 `rFutureHighLowUnitChange` 输出：

```text
x_atr_high
x_atr_low
high
low
```

输入：

```text
units
highs
lows
prices
```

注意：

- `prices[0]` 是 anchor 交易参考价。
- `units[0]` 是 anchor 时刻的单位尺度。
- pyta2 不关心 `unit` 是 ATR、波动率还是其他量。

### trigger.py

| fintools | pyta2 | 说明 |
| --- | --- | --- |
| `reBoundTrigger` | `rBoundTrigger` | 上下边界首次触发 |
| `reTrailingTrigger` | `rTrailingTrigger` | 追踪止损/止盈触发 |

`rBoundTrigger` 推荐输入：

```text
units
opens
highs
lows
closes
```

参数：

```text
x_unit_ub
x_unit_lb
n_forward=None
```

输出：

```text
trigger          int8, {-1, 0, 1}
change           float
trigger_location int64
```

`rTrailingTrigger` 推荐输入：

```text
units
opens
highs
lows
closes
```

参数：

```text
direction
x_unit_retrace
n_forward=None
slippage_ratio=0.0
```

输出：

```text
trigger
profit
trigger_price
trigger_ref_price
trigger_location
trigger_ref_location
```

路径触发类可以保留 OHLC 输入，因为 OHLC 是一种通用路径压缩格式，不绑定 sigma2 K 线 family。

路径触发必须定义同一根 OHLC 内的确定性顺序。

第一阶段采用从 `fintools` 迁移来的规则：

```text
if high - open < open - low:
    认为 high 先发生，low 后发生
else:
    认为 low 先发生，high 后发生
```

含义：

- open 总是先于 high/low 检查。
- close 总是作为该压缩路径的最后价格。
- 当同一根 OHLC 内上下边界都可能触发时，按上述 high/low 先后顺序决定首次触发方向。
- 距离相等时走 `else` 分支，即 low 先发生。
- `trigger_location` 是相对 anchor 的未来偏移，第一根未来 OHLC 的 location 为 1。

## n_forward 与 window

推荐规则：

```text
n_forward >= 1
window = n_forward + 1
```

含义：

```text
values[0]       anchor
values[1]       下一点
values[n_forward] 第 n_forward 点
```

对于未来窗口统计：

```text
values[1:n_forward+1]
```

trigger 类保留原始 `n_forward=None` 语义。

含义：

- `window=None`。
- `backward_rolling_apply()` 向 effect 传入从当前 anchor 到序列末尾的完整后缀。
- effect 自己决定使用多少未来数据。

注意：

- 机器学习训练切分时，调用方必须先切分数据再计算 target，避免 `n_forward=None` 跨 split 使用未来数据。
- 除原始 effect 已定义 `n_forward=None` 的场景外，不应随意给固定窗口 effect 增加该语义。

## 收益类型

`rFutureReturn` 是 `reRoChg` 的兼容别名，primitive 层遵守原始输出：

```text
pct_change
```

语义：

```python
values[n_forward] / values[0] - 1
```

不在 primitive 层支持 `return_type="log"`。如果 sigma2 或训练框架需要 log return，应在 family 包装层或独立 effect 中显式定义，避免与 `backward_rolling_apply(return_type=...)` 的输出容器参数混淆。

- `rFutureReturn(return_type=...)` 中的 `return_type` 表示收益计算类型。
- `backward_rolling_apply(return_type=...)` 中的 `return_type` 继承 pyta2 现有 `forward_rolling_apply()` 语义，表示输出容器类型。
- 二者位于不同参数空间；通过 runner 传入 effect 参数时，应写入 `param_kwargs={"return_type": "log"}`。
- 不把收益类型命名为 `mode`，因为 `type` 对用户更直观，也更贴近 pyta2 既有命名风格。

## 缺失值策略

通用规则：

- 未来窗口不足时返回 NaN 或 schema 对应缺失值。
- 多输出 effect 返回完整 arity 的缺失 tuple。
- 计算逻辑优先继承 `fintools`，但 pyta2 输出必须满足 `schema` arity；因此多输出 effect 不返回裸 `None`。
- 不吞掉形状错误。
- 输入长度不足是正常边界，不是异常。
- 参数非法是异常，例如 `n_forward < 1`、`k > n_forward`、`x_unit_ub <= 0`。

推荐内部工具：

```python
make_output_na(schema)
```

但第一阶段可以复用已有输出处理逻辑。

## schema 设计

继续使用 `pyta2.base.Schema` 和 `pyta2.utils.space.Space`。

示例：

```python
schema=[
    ("pct_change", Space.Scalar(dtype=np.float64)),
]
```

多输出示例：

```python
schema=[
    ("trigger", Space.Scalar(dtype=np.int8)),
    ("profit", Space.Scalar(dtype=np.float64)),
    ("trigger_price", Space.Scalar(dtype=np.float64)),
    ("trigger_ref_price", Space.Scalar(dtype=np.float64)),
    ("trigger_location", Space.Scalar(dtype=np.int64)),
    ("trigger_ref_location", Space.Scalar(dtype=np.int64)),
]
```

不引入 `fintools` 的 `Domain`。

原因：

- pyta2 已经有 `Space`。
- sigma2 也复用 pyta2 `Schema` / `Space`。
- 引入第二套 domain 会制造概念重复。

## 用户 API 示例

### 批量未来收益

```python
from pyta2.base import backward_rolling_apply
from pyta2.effect import rFutureReturn

y = backward_rolling_apply(
    len(closes),
    rFutureReturn,
    param_args=[5],
    input_args=[closes],
)
```

### 批量未来最大涨幅

```python
from pyta2.effect import rFutureHighChange

y = backward_rolling_apply(
    len(closes),
    rFutureHighChange,
    param_args=[20],
    input_args=[highs, closes],
)
```

### 批量边界触发

```python
from pyta2.effect import rBoundTrigger

out = backward_rolling_apply(
    len(closes),
    rBoundTrigger,
    param_args=[2.0, 1.0, 20],
    input_args=[units, opens, highs, lows, closes],
    return_type="dict",
)
```

## sigma2 绑定示例

pyta2 不实现这部分，但设计必须支持它。

K 线未来收益：

```python
class rForwardReturn(rKlineEffect):
    def __init__(self, horizon, field="close", **kwargs):
        super().__init__(
            effect=rFutureReturn(horizon),
            bind={"values": field},
            **kwargs,
        )
```

盘口中间价未来收益：

```python
class rMidForwardReturn(rOrderBookEffect):
    def __init__(self, horizon, **kwargs):
        super().__init__(
            effect=rFutureReturn(horizon),
            bind={"values": "mid_price"},
            **kwargs,
        )
```

K 线路径触发：

```python
class rBoundTrigger(rKlineEffect):
    def __init__(self, x_unit_ub, x_unit_lb, n_forward=None, unit="atr", **kwargs):
        super().__init__(
            effect=pyta2.effect.rBoundTrigger(x_unit_ub, x_unit_lb, n_forward),
            bind={
                "units": unit,
                "opens": "open",
                "highs": "high",
                "lows": "low",
                "closes": "close",
            },
            **kwargs,
        )
```

## 兼容策略

`pyta2.effect` 的 primitive 层以 `fintools` 原始 effect 语义为主。

可以在 pyta2 内提供 `rFuture*` 兼容别名：

```python
rFutureChange = reChg
rFutureReturn = reRoChg
rFutureSMA = reSMA
rFutureEMA = reEMA
```

别名规则：

- `re*` 名称和参数语义按原始 effect 稳定。
- `rFuture*` 只是 pyta2 风格导入别名，不引入第二套公式或输出键。
- family/user-facing 字段重命名放在 sigma2 等上层。
- 不迁移 `fintools` 中明显未完成或错误的 `zg_bound_trigger.py`。

## 不迁移内容

以下内容不进入 pyta2.effect 第一阶段：

- `fintools` 的 `BaseFactor`、`BaseSignal`。
- `fintools` 的 `Domain` / `RangeDomain` / `SetDomain`。
- 与具体 broker、backtest、dataset、profile 相关的内容。
- `zg_bound_trigger.py` 中未完成且引用未定义变量的逻辑。
- 与 sigma2 `TargetData`、`FeatureData`、IC、RL、minbt 相关的对象。

## Contract Tests

`pyta2.effect` 至少需要锁定以下契约。

基类：

- `rEffect` 与 `rIndicator` 共享 `schema`、`output_keys`、`return_dict`、`outputs`、`required_window` 心智。
- `rEffect.rolling()` 调用 `backward()`。
- `rEffect.meta_info["direction"] == "backward"`。
- `make_dict_output()` 对标量、多输出、mapping 的处理与 `rIndicator` 一致。
- `rEffect.outputs` 记录反向调用顺序，不被测试为原始时间正序。

Runner：

- `backward_rolling_apply()` 从右向左调用同一个 effect 实例。
- 返回结果按原始时间正序排列。
- 固定 `n_forward` effect 只切片 `i:i+required_window`，不默认传完整 `i:` 后缀。
- `window=None` effect 传入 `i:` 后缀。
- input args / kwargs 长度校验与 `forward_rolling_apply()` 一致。
- `return_type="tuple" | "dict" | "dataframe"` 与现有 `get_outputs()` 语义一致。
- `return_meta_info=True` 返回输出和 `meta_info`。

基础 effect：

- `rFutureReturn(n_forward=1)` 使用下一点而不是当前点。
- `rFutureReturn(n_forward=n)` 使用 `values[n] / values[0] - 1`。
- `rFutureReturn` 输出 key 为 `pct_change`。
- 未来窗口不足返回 NaN。
- `rFutureSMA(n)` 使用 `values[1:n+1]`，不包含 anchor。
- `rFutureEMA` 在 `backward_rolling_apply()` 中保持反向状态。
- `rFutureEMA` 首次有效调用以未来窗口 SMA 初始化，然后按原始公式递推。
- `rFutureKthTop(k)` 必须校验 `1 <= k <= n_forward`。

路径 effect：

- `rBoundTrigger` 只检查未来窗口，不检查 anchor 自身。
- 同一根 OHLC 内上下边界都可触发时，按 `high - open < open - low` 判断 high/low 先后；距离相等时 low 先发生。
- `rTrailingTrigger` 输出 arity 和 schema 必须与原始 `fintools` 一致。
- trigger 支持 `n_forward=None`，表示检查完整可见未来后缀。

## 第一阶段实施顺序

建议先做最小闭环。

1. 新增 `pyta2.base.effect.rEffect`。
2. 在 `pyta2.base.__init__` 导出 `rEffect`。
3. 在 `pyta2.base.utils` 新增 `backward_rolling_apply()`。
4. 新增 `pyta2.effect.change`，实现 `rFutureChange`、`rFutureReturn`、`rFutureUnitChange`。
5. 新增 `pyta2.effect.ma`，实现 `rFutureSMA`、`rFutureEMA`、`rFutureWMA`。
6. 新增 `pyta2.effect.trigger`，迁移并整理 `rBoundTrigger`。
7. 补充 contract tests。
8. 再考虑 stats、rank、path、`rTrailingTrigger` 和兼容别名。

第一阶段不做：

- sigma2 绑定。
- TargetData。
- IC 分析。
- RL reward。
- 全量 `fintools` 兼容。

## 最终判断

`pyta2.effect` 应该成为 pyta2 的反向 rolling primitive 层。

最终关系：

```text
pyta2.rIndicator.forward()
  通用正向 feature 算子

pyta2.rEffect.backward()
  通用反向 target / outcome 算子

sigma2
  按 kline / orderbook / trade 把标准化数据字段绑定到 pyta2 算子
```

这样可以同时满足：

- pyta2 保持数据无关的通用 rolling 算子库定位。
- sigma2 保持按输入数据类型分类的自洽结构。
- 监督学习训练所需的 target / outcome 有稳定、可复用的底层实现。
- `fintools effect` 中已有经验被吸收，但不会把旧目录结构和命名问题带入 pyta2。
