# sigma2 总体设计

更新时间：2026-07-07 12:01 CST

## 状态

本文是 `docs/design` 下唯一当前有效的总体设计文档。旧版阶段性设计已经移入 `docs/design/backup/`，仅保留历史追溯价值，不作为后续实现依据。

关键结论：

- sigma2 core 不是 `FeatureSet`。
- sigma2 core 是一套轻量、可继承、类似 `pyta2.base.rIndicator` 的有状态 rolling signal 基类体系。
- `rSignal` 保留 `rIndicator` 的核心心智：`window`、`schema`、`output_keys`、`required_window`、`forward()`、`reset()`、`reset_extras()`、`outputs`、`g_index`、`return_dict`、`make_dict_output()`、`meta_info`。
- sigma2 不保留 `rolling()` 作为通用 core API；唯一公共状态推进入口是 `step()`。
- `forward()` 是子类实现计算逻辑的 hook，类似神经网络 forward；直接调用 `forward()` 不推进 core 生命周期状态、不写输出缓存、不处理 `return_dict`。
- `update()` 不进入 core。K 线未完成周期修正、盘口增量应用、实盘 preview 等由 adapter、stream builder 或 preview runner 处理。
- `window` 表示产生有效输出所需的最少 step 数，不表示 core 默认维护原始输入历史。
- 需要原始 OHLCV 历史序列的 K 线信号通过 `rKlineWindowSignal` opt-in 维护窗口；orderbook/trades 等 family 默认不承担历史 window 成本。
- sigma2 不新增公共环形缓存抽象；内部 rolling 缓存优先复用 pyta2 已有的 `NumpyDeque`、`DequeTable`、`VectorTable` 等工具。
- sigma2 的源码组织也应以信号为中心：根目录直接是信号输入类型分类，例如 `sigma2/kline/`、`sigma2/orderbook/`、`sigma2/trade/`；每个具体信号一个文件。
- `base/`、`signals/`、`families/`、`adapters/` 不作为长期一级目录；非信号基础设施收拢到 `core/` 和 `utils/`。
- `core/` 是唯一核心目录：`rSignal`、family 基类、pyta2 通用信号基类都在 `core/`；pyta2 resolver 放在 `utils/`。
- 当前阶段不做全面 pyta2 指标 catalog 迁移；先稳定信号目录、继承契约和少量示例信号。
- `FeatureSet`、DataFrame batch、ML 矩阵生成、minbt adapter 都是应用层能力，应该消费 core，而不是定义 core。

## 设计目标

sigma2 的最低稳定单元是“信号类”，而不是“特征集合”。因此整体设计要同时稳定两件事：

1. 用户如何继承一个类写出信号。
2. 用户和二次开发者如何在源码树中找到、阅读、扩展一个信号。

用户和二次开发者应该可以这样使用：

```python
from sigma2 import rKlineWindowSignal, Space


class rGap(rKlineWindowSignal):
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

    def reset_window_extras(self):
        pass

    def forward(self, opens, highs, lows, closes, volumes):
        if len(closes) < 2:
            return float("nan")
        return opens[-1] / closes[-2] - 1.0


signal = rGap(return_dict=True)
row = signal.step(open=101.0, high=103.0, low=100.0, close=102.0, volume=1200.0)
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
| 信号分类层 | `sigma2.kline.*` / `sigma2.orderbook.*` / `sigma2.trade.*` | 用户主入口，随信号逐个稳定 | 具体信号类；每个信号一个文件 |
| 核心层 | `sigma2.core.*` | 最先稳定 | `rSignal`、family 基类、schema、输出、生命周期、pyta2 通用信号基类；后续可加入 engine/registry |
| 工具层 | `sigma2.utils.*` | 独立演进 | pyta2 resolver、缓存工具封装、通用辅助函数 |
| 应用能力 | `sigma2.core` 的子模块或后续独立包 | 最后稳定 | `FeatureSet`、DataFrame batch、online state、训练矩阵、minbt adapter |

稳定性顺序：

1. 先稳定核心层。
2. 再稳定常用内置信号。
3. 再稳定 pyta2 信号基类和 resolver。
4. 最后稳定 `FeatureSet` 等应用层门面。

原因：应用层需求最容易随真实使用变化，核心信号继承契约一旦稳定，用户今天写的信号就能被未来任意应用层复用。

## 整体源码结构

sigma2 的源码树应直接表达用户心智：打开包根目录，首先看到的是可以使用和扩展的信号分类。非信号对象不能挤占根目录的主要位置，应放入 `core/` 或 `utils/`。

目标结构：

```text
sigma2/
  __init__.py
  core/
    __init__.py
    signal.py
    kline.py
    orderbook.py
    trade.py
    pyta2.py
  utils/
    __init__.py
    pyta2.py
  kline/
    __init__.py
    gap.py
    return_.py
    sma.py
    pyta2/
      __init__.py
      sma.py
  orderbook/
    __init__.py
    book_spread.py
  trade/
    __init__.py
    trade_signed_volume.py
```

稳定规则：

- `sigma2.<family>` 是具体信号的主发现入口。
- 根目录下的业务命名目录优先留给信号输入类型分类，例如 `kline`、`orderbook`、`trade`、未来的 `funding_rate`、`news`。
- 每个具体信号一个文件；文件内只放该信号及其非常小的私有辅助逻辑。
- 各级 `__init__.py` 只负责导出，不承载具体信号实现。
- 顶层 `sigma2.__init__` 可以 re-export 常用信号，但顶层导出不是源码组织依据。
- 文件名使用小写语义名，类名使用 `rXxx`，保持与 `pyta2.base.rIndicator` 的 rolling 类心智一致。
- Python 关键字冲突用后缀处理，例如 `return_.py` 中定义 `rReturn`。
- 新增输入数据类型时新增根级 family 目录和对应 family 基类，不修改已有 family 的输入契约。
- 新增具体 pyta2 快捷信号时放在所属数据类型目录下，例如 K 线 pyta2 SMA 位于 `kline/pyta2/sma.py`。
- `core/` 是唯一核心目录，放稳定基类、输入契约和后续运行时编排，例如 `rSignal`、`rKlineSignal`、`rOrderBookSignal`、`rTradeSignal`、`rPyta2Signal`，未来可加入 engine、registry、batch replay、FeatureSet、minbt adapter。
- `utils/` 只放无状态或低状态辅助能力，例如 pyta2 name resolver、缓存工具选择、导入兼容。
- 不再新增 `base/` 作为公共一级目录；`base` 和 `core` 同时存在会制造不必要的层级歧义。
- 不再新增 `signals/` 作为公共一级目录；它会让用户多理解一层空泛概念。

导入层级：

```python
from sigma2 import rSMA
from sigma2.kline import rSMA
from sigma2.kline.sma import rSMA

from sigma2 import rPyta2SMA
from sigma2.kline.pyta2 import rPyta2SMA
```

推荐二次开发方式：

```text
1. 先判断输入数据类型：kline / orderbook / trade / 新 family。
2. 继承对应 family 基类。
3. 在 `<family>/<signal>.py` 中实现一个 `rSignal` 子类。
4. 在该 family 的 `__init__.py` 中导出。
5. 如果是常用稳定信号，再由 `sigma2` 顶层导出。
```

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

### 方案 C：rSignal-first + step

```python
class rMySignal(rKlineSignal):
    def forward(self, open, high, low, close, volume):
        ...


signal.step(open=..., high=..., low=..., close=..., volume=...)
```

优点：

- 与 `pyta2.base.rIndicator` 的有状态指标心智一致。
- 用户继承一个类即可定义信号。
- 用户、engine、adapter 只有一个公共入库入口：`step()`。
- `forward()` 保留为清晰的计算 hook，类似神经网络 forward。
- 自定义信号、pyta2 适配信号、组合信号可以统一到同一个对象模型。
- 上层 `FeatureSet`、ML batch、minbt adapter 都能消费同一个信号对象。
- 不把 orderbook/trades 迫使成历史窗口模型。

缺点：

- DataFrame 一键训练矩阵不是 core 直接解决的问题。
- 需要额外应用层处理多信号编排和输出矩阵。
- 需要通过文档和 contract tests 明确 engine 只能调用 `step()`，不能把 `forward()` 当入库入口。

结论：采用，作为稳定核心。

### 方案 D：rolling/update-first

```python
signal.rolling(opens, highs, lows, closes, volumes)
signal.update(open, high, low, close, volume)
```

优点：

- 与 pyta2 表面方法名更接近。
- 对传统 K 线窗口型指标直观。

缺点：

- `rolling()` 暗示输入是历史窗口序列，不适合 orderbook/trades 高频事件流。
- `update()` 在 orderbook 语境中容易被理解为应用盘口 delta。
- 同时暴露 `rolling()`、`update()`、`forward()` 会诱导用户交替调用，破坏状态一致性。
- `update(mode="append/update")` 会把追加新事件和修正当前事件混在一个入口里，迫使所有 signal 支持回滚或替换状态。

结论：不采用。`rolling()` 不进入通用 core；`update()` 不进入 core。

### 方案 E：纯函数-first

```python
def gap(opens, highs, lows, closes, volumes):
    ...
```

优点：

- 最轻。
- 易测试。

缺点：

- 状态、缓存、schema、warmup、元信息都要额外约定。
- 无法自然表达 online 生命周期。
- 与 pyta2 的 `rIndicator` 结构不一致。

结论：可作为内部实现辅助，不作为核心公共接口。

## 源码组织方案比较

### 方案 A：按 family 聚合到单文件

```text
kline.py
orderbook.py
trade.py
```

优点：

- 初期文件少。
- 最小实现速度快。

缺点：

- 信号数量增加后，一个文件会快速膨胀。
- 二次开发者难以判断新增信号应该插入哪里。
- 不利于 review 单个信号的算法、schema、测试边界。
- 与 pyta2 “一个指标一个文件”的长期结构不一致。

结论：只适合最小原型，不作为长期结构。

### 方案 B：使用 `signals/` 作为一级目录

```text
signals/
  kline/
    sma.py
    return_.py
  orderbook/
    book_spread.py
```

优点：

- 层级语义完整，所有信号在一个目录下。
- 对内部实现者来说比较整齐。

缺点：

- `signals` 是空泛包装层，用户已经知道自己要找的是信号，不应再被迫进入一层 `signals/`。
- 二次开发时，根目录不能直接表达 sigma2 最重要的扩展轴：输入数据类型。
- 与“根目录就是信号分类”的目标不一致。

结论：不采用。

### 方案 C：根目录按算法类别分组

```text
trend/
momentum/
stats/
```

优点：

- 接近 pyta2 技术指标分类。
- 对传统 K 线指标比较自然。

缺点：

- sigma2 的核心扩展轴是输入数据类型，不只是算法类型。
- orderbook、trade、funding rate、news 等信号很难统一放入传统 TA 分类。
- 同名算法在不同输入类型下可能输入契约完全不同。
- 容易把 sigma2 拉回“pyta2 指标集合”的心智，而不是通用信号库。

结论：不作为第一层目录。未来可在 family 内部按需增加二级分类，但不能替代 family 分组。

### 方案 D：根目录按输入数据类型 family 分组，每个信号单文件

```text
kline/
  sma.py
  return_.py
orderbook/
  book_spread.py
trade/
  trade_signed_volume.py
core/
utils/
```

优点：

- 与“输入类型决定 family”的核心设计一致。
- 每个目录天然共享同一套 `step()` 输入契约。
- 新增 orderbook、trade、news、funding rate 等输入类型时只新增目录和 family，不需要修改既有信号。
- 每个信号单文件，便于 review、测试、文档和二次开发。
- 保留与 pyta2 类似的可发现性，但不把 sigma2 限制为 K 线 TA 指标库。
- 根目录直接呈现用户关心的信号分类，符合二次开发直觉。
- `core/`、`utils/` 明确承载非信号能力，用户不会误把 engine/adapter 当信号分类。

缺点：

- 初期文件数量更多。
- 某些算法分类信息不在第一层目录中，需要通过文档、registry 或文件命名补充。
- 根目录需要控制命名纪律，避免未来把应用层概念也放到一级目录。

结论：采用。第一层按输入数据类型 family 分组，第二层才允许按来源或算法类型细分，例如 `kline/pyta2/sma.py`。

## 稳定核心对象

### rSignal

`rSignal` 是 sigma2 的核心公共开发接口。它应尽可能保留 pyta2 `rIndicator` 的状态、输出和元信息心智，但用 `step()` 替代 `rolling()` 作为唯一公共状态推进入口。

必须保持一致的概念：

- `window`
- `schema`
- `buffer_size`
- `extra_window`
- `buffer_factor`
- `return_dict`
- `g_index`
- `step()`
- `forward()`
- `reset()`
- `reset_extras()`
- `full_name`
- `outputs`
- `output_keys`
- `required_window`
- `meta_info`
- `make_dict_output()`

sigma2 的必要差异：

- 输入字段不在 `rSignal` 定义，而由 family 子类定义。
- `step()` 是唯一公共状态推进入口。调用一次表示输入流推进一个新观测点或事件。
- `forward()` 是子类计算 hook。直接调用 `forward()` 不进入 core 生命周期。
- `rolling()` 不属于通用 core API。
- `update()` 不属于 core API。
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
        buffer_size: int | None = 1,
        extra_window: int = 0,
        buffer_factor: int = 2,
        return_dict: bool = False,
    ):
        ...

    def step(self, *args, **kwargs):
        self.g_index += 1
        output = self._step_forward(*args, **kwargs)
        dict_output = self.make_dict_output(output)
        self._outputs.append(dict_output)
        return dict_output if self.return_dict else output

    def _step_forward(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

    def forward(self, *args, **kwargs):
        raise NotImplementedError

    def reset(self):
        self.g_index = -1
        self._outputs.clear()
        self.reset_extras()

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
    def latest(self):
        ...

    @property
    def output_keys(self):
        ...

    @property
    def required_window(self):
        return self.window + self.extra_window

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
- `latest`
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
- 不改变 `step()`、`forward()`、`reset()` 的核心生命周期语义。
- `step()` 是唯一会推进 `g_index`、调用 `forward()`、写入 `outputs`、处理 `return_dict` 的公共方法。
- `_step_forward()` 是 family 或高级子类的内部适配 hook，可以维护输入窗口或转换输入，然后调用 `forward()`。
- `forward()` 不推进 `g_index`，不写 `outputs`，不处理 `return_dict`；family 基类不应在 `forward()` 中维护输入历史。
- `window` 表示产生有效输出需要的最少 step 数，不等于 core 必须保存的原始输入历史长度。
- `meta_info` 可以新增字段，但不能删除已有字段。
- `make_dict_output()` 的输出 key 必须始终等于 `output_keys`。
- `return_dict` 默认值与 `rIndicator` 保持一致；应用层需要 dict 时显式传入 `return_dict=True` 或调用 `make_dict_output()`。
- 一个 `rSignal` 实例是单输入流状态对象。多 symbol、多 venue、多策略实例由应用层 clone 或 factory 管理。
- `step()` 默认不复制可变输入；如果信号需要长期保存输入，必须自行复制所需部分。

### family 子类

family 子类负责定义输入契约。`rSignal` 不直接知道 K 线、订单簿或成交字段。

设计关系：

```text
InputType / MarketDataKind -> SignalFamily -> rSignal subclass
```

公共字段统一使用 `family`。旧文档中的 `data_kind` 可作为内部兼容别名，但不应成为稳定公共命名。

family 子类需要定义：

- `family`
- `step_input_keys`
- `step(...)`
- `forward(...)`

同一 family 下的普通信号应共享同一套 `step` 输入契约。确实不同的输入形态应定义子 family，例如 `orderbook_snapshot` 与 `orderbook_delta`。

## K 线核心

### rKlineSignal

`rKlineSignal` 是第一批必须冻结的 family 子类。它不默认维护 OHLCV 历史窗口。

```python
class rKlineSignal(rSignal):
    family = "kline"
    step_input_keys = ("open", "high", "low", "close", "volume")

    def step(self, *, open, high, low, close, volume):
        return super().step(open, high, low, close, volume)

    def forward(self, open, high, low, close, volume):
        raise NotImplementedError
```

稳定语义：

- `step()` 接收单个已确定 K 线点：`open, high, low, close, volume`。
- `step()` 调用一次表示输入流推进到下一根已确定 K 线。
- `rKlineSignal` 不默认维护 `opens/highs/lows/closes/volumes` 历史。
- 直接使用当前点即可计算的信号继承 `rKlineSignal`。
- `open` 作为公共关键字保留；实现内部可用 `open_` 避免遮蔽内置函数。

### rKlineWindowSignal

需要 K 线历史序列的信号继承 `rKlineWindowSignal`。

```python
from pyta2.utils.deque import DequeTable


class rKlineWindowSignal(rKlineSignal):
    def reset_extras(self):
        self._window = DequeTable(
            maxlen=self.required_window,
            buffer_factor=self.buffer_factor,
            schema={
                "open": "float64",
                "high": "float64",
                "low": "float64",
                "close": "float64",
                "volume": "float64",
            },
        )
        self.reset_window_extras()

    def _step_forward(self, open, high, low, close, volume):
        self._window.append({
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })
        return self.forward(
            self._window["open"],
            self._window["high"],
            self._window["low"],
            self._window["close"],
            self._window["volume"],
        )

    def reset_window_extras(self):
        raise NotImplementedError

    def forward(self, opens, highs, lows, closes, volumes):
        raise NotImplementedError
```

稳定语义：

- `rKlineWindowSignal` 是 opt-in 的历史窗口能力。
- `_step_forward()` 负责追加 OHLCV 历史窗口，然后调用 `forward()`。
- `forward()` 接收标准 K 线序列：`opens, highs, lows, closes, volumes`。
- 直接调用 `forward(opens, highs, lows, closes, volumes)` 不追加内部窗口，不进入 core 生命周期。
- 内部窗口建议使用 `pyta2.utils.deque.DequeTable`，不要新增独立公共环形缓存抽象。
- pyta2 adapter 和 SMA、ATR、MACD 等窗口型 K 线信号优先基于 `rKlineWindowSignal` 实现。
- `rKlineWindowSignal` 只是 K 线 family 的便利基类，不把历史窗口要求扩散到 orderbook/trades。

这意味着用户今天继承 `rKlineSignal` 或 `rKlineWindowSignal` 写出的信号，应能长期复用到：

- 手写实时策略
- `SignalEngine`
- `FeatureSet`
- minbt adapter
- ML batch runner

## 内部缓存工具选择

sigma2 的公共 API 不暴露具体缓存容器，但实现时应优先复用 pyta2 已有工具，避免新建一套公共环形缓存抽象。

推荐分工：

- `pyta2.utils.deque.NumpyDeque`：单列 rolling 状态，例如某个信号内部只需要维护一列价格、收益或中间变量。
- `pyta2.utils.deque.DequeTable`：多列 rolling 窗口，例如 OHLCV、输出短缓存、需要按列读取的实时窗口。
- `pyta2.utils.vector.VectorTable`：无 `maxlen` 的列式长表，适合应用层 batch、ML 矩阵构造或历史结果收集，不属于 core signal 状态。

约束：

- `rSignal.outputs` 的实现应尽量沿用 pyta2 `rIndicator` 心智，优先使用 `DequeTable`。
- `rKlineWindowSignal` 内部 OHLCV 窗口优先使用 `DequeTable`。
- 具体容器是内部实现细节；普通信号作者只需要实现 `forward(...)`，不应被迫理解 `DequeTable`。
- 如果后续需要兼容非 NumPy 对象或极端性能路径，可以在内部增加轻量 wrapper，但 wrapper 不应作为第一版公共 API。

## 同周期更新与 preview

同周期 K 线修正场景真实存在，例如实盘中当前分钟 K 线的 close 随 tick 更新。但该能力不进入 `rSignal` core。

原因：

- `step()` 的含义是追加一个新观测点或事件；修正当前观测点是另一种状态操作。
- 对 SMA 这类纯窗口信号，替换最后一根 K 线似乎可行；但对 EMA、ATR、MACD、组合信号、pyta2 adapter，上一轮输入已经推进内部状态，不能简单替换最后输出。
- 如果 core 暴露 `update()` 或 `step(mode="update")`，所有信号都必须定义 rollback、replace-last-output、内部状态重算等语义，复杂度过高。
- ML batch 默认使用 finalized data，不需要未完成 K 线修正语义。

推荐处理方式：

```python
builder.update_tick(dt, price, volume)

if builder.closed_kline is not None:
    signal.step(**builder.closed_kline)
```

实盘需要查看未完成 K 线时，应使用 adapter 或 preview runner：

```python
partial = builder.current_kline()
preview = preview_runner.compute(signal_factory, partial)
```

约束：

- preview 不写入正式 `rSignal` 状态。
- 同周期修正、撤单、盘口 delta 应在 stream builder 或对应 delta family 中表达。
- core 不提供 `update()`。

## 订单簿与成交扩展

orderbook/trade 现在要考虑扩展框架，但不应在没有足够真实信号前过度冻结 L2、L3、增量订单流等细节。

稳定原则：

- 新 family 必须通过新的 family 子类表达，而不是往 `rKlineSignal` 塞字段。
- 每个 family 子类必须定义自己的 `step_input_keys`。
- 同一 family 下的信号必须共享同一套 `step()` 输入契约。
- 应用层只能根据 `family` 路由，不能写死外部框架名。
- orderbook/trade 默认不维护历史 window；时间窗口、事件窗口和内部状态由具体 signal 自行实现。

第一批候选输入契约：

```python
class rOrderBookSignal(rSignal):
    family = "orderbook"
    step_input_keys = ("bids", "asks")

    def step(self, *, bids, asks):
        return super().step(bids, asks)

    def forward(self, bids, asks):
        raise NotImplementedError
```

约定：

- `bids` / `asks` 是当前快照的档位序列，按最优价优先排序。
- 每个档位的最小形态是 `(price, size)`。
- 如果需要长期保存盘口快照或派生状态，由具体 signal 自行复制所需字段。
- 盘口增量不是该 family 的默认语义；需要时定义 `rOrderBookDeltaSignal` 或由 adapter 先构造快照。

```python
class rTradeSignal(rSignal):
    family = "trade"
    step_input_keys = ("price", "volume", "side")

    def step(self, *, price, volume, side=None):
        return super().step(price, volume, side)

    def forward(self, price, volume, side=None):
        raise NotImplementedError
```

约定：

- `side` 先采用 `"buy"` / `"sell"` / `None`。
- 如果交易所一次推送多笔成交，应由 adapter 拆成多次 `step()`，或定义 `rTradeBatchSignal` 子 family。
- 更复杂的成交批次、逐笔 id、主动买卖识别可以通过子 family 或可选字段扩展，不能破坏上述最小契约。

冻结策略：

- `rKlineSignal` 和 `rKlineWindowSignal` 在 v0.1 直接冻结。
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
- `outputs` 是信号自身的短输出缓存，不是训练矩阵存储。batch 矩阵由应用层收集。

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
rPyta2SMA(20, field="close", name="sma_close_20")

pyta2_signal(
    "SMA",
    params={"n": 20},
    field="close",
)
```

稳定边界：

- `rPyta2Signal` 对外仍是 `rKlineWindowSignal`。
- `rPyta2Signal.step(open, high, low, close, volume)` 是公共入口。
- pyta2 信号基类内部可以维护 OHLCV 窗口并调用 pyta2 指标的 `rolling()`。
- `rPyta2Signal` 是通用 pyta2 信号基类，位置应在 `sigma2.core.pyta2`。
- pyta2 名称解析、导入兼容等无状态辅助放在 `sigma2.utils.pyta2`。
- `rPyta2SMA` 这类具体快捷类是用户可继承、可阅读的信号类，位置应在所属输入数据类型目录，例如 `sigma2.kline.pyta2.sma`。
- `pyta2_signal()` / `resolve_pyta2_indicator()` 是工具或构造接口，负责把 pyta2 名称或 class 解析为 rolling indicator class。
- `field` / `inputs` 是 adapter 参数，不进入普通 K 线信号接口。
- 如果 pyta2 后续暴露顶层 `rSMA` 或 name registry，sigma2 只需要替换 resolver，不应改变 `rPyta2SMA` 用户代码。
- sigma2 不重复维护 pyta2 指标定义，只读取其 `schema`、`output_keys`、`required_window`、`meta_info`。
- 当前阶段只保留 `rPyta2SMA` 作为类式快捷适配样例，不把扩展其它 `rPyta2Xxx` catalog 作为高优先级工作。
- 未来新增具体 pyta2 快捷信号必须逐个评审输入契约、输出 schema 和测试，不做机械迁移。

## 应用层位置

`FeatureSet` 仍然有价值，但当前尚未实现。后续实现时，它应作为 core 消费者，而不是反向定义 `rSignal`。

后续推荐位置：

```python
from sigma2.core import FeatureSet
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

`FeatureSet` 是后续应用层便利门面，用于把一组标准信号对象转成训练矩阵或在线特征行。

后续推荐形态：

```python
from sigma2.core import FeatureSet

features = FeatureSet([
    rReturn(n=1, name="ret_1", return_dict=True),
    rReturn(n=5, name="ret_5", return_dict=True),
    rPyta2SMA(20, field="close", name="sma_close_20", return_dict=True),
])

X = features.batch(df, schema=schema)
state = features.online()
```

约束：

- `FeatureSet` 接收 `rSignal` 实例或能构造 `rSignal` 的声明。
- `FeatureSet.batch()` 可以 replay `step()`，也可以后续向量化，但输出语义必须与 step replay 一致。
- `FeatureSet` 可以默认使用 `return_dict=True` 的信号实例，但不能改变 `rSignal` core 的默认心智模型。
- warmup 裁剪、标签对齐、样本过滤属于应用层策略，不能隐藏到 core。
- 多 symbol 场景下，一个 signal 实例只能绑定一个输入流；`FeatureSet` 应通过 factory/clone 为不同 symbol 创建独立状态。

### DataSchema

`DataSchema` 属于应用层数据标准化，不属于 core。

职责：

- 描述用户原始 DataFrame / dict / 框架数据到 family 输入字段的映射。
- 处理时间字段、symbol 字段和可用时间字段。
- 为 `FeatureSet.batch()`、adapter 和 online runner 构造 family 子类需要的标准 `step()` 输入。

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
- `DataSchema` 不能反向影响 `rSignal` / family 子类的方法签名。

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
- minbt 的 `bar/bars` 命名只出现在 `sigma2.core.minbt`。
- adapter 只负责把 minbt 数据翻译为 sigma2 family `step()` 输入，并把信号输出交还策略。

推荐位置：

```python
from sigma2.core.minbt import MinbtFeatureAdapter
```

禁止：

- `rSignal`、family 子类、`FeatureSet` core 流程中出现 `update_minbt_bars(...)`。
- 在 sigma2 core 中出现 `Broker`、下单、持仓、资金管理概念。

## 版本与兼容性

在 v0 阶段也要人为维持兼容规则。

推荐版本规划：

| 版本 | 冻结内容 |
| --- | --- |
| `0.1.x` | `rSignal.step()`、`rKlineSignal`、`rKlineWindowSignal`、schema/output、基础 K 线自定义信号 |
| `0.2.x` | pyta2 信号基类、常用 K 线内置信号、最小 `SignalEngine` |
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
- 继承 `rKlineWindowSignal` 的自定义信号可以只实现窗口序列版 `forward()` 和 `reset_window_extras()`。
- `step(open, high, low, close, volume)` 调用一次只推进一次 `g_index`。
- 直接调用 `forward()` 不改变 `g_index`、`outputs` 或 `return_dict` 行为。
- family 基类不在 `forward()` 中维护输入历史；输入窗口维护只能发生在 `step()` 调用链内的内部 hook。
- `rKlineWindowSignal.step()` 与手动维护窗口后调用窗口序列版 `forward()` 输出一致。
- `rKlineWindowSignal` 默认内部窗口实现不引入新的公共环形缓存抽象，优先基于 `DequeTable`。
- `FeatureSet.batch()` 的 replay 只能调用 `step()`，不能调用 `forward()`。
- `make_dict_output()` 对标量、tuple、mapping 的行为稳定。
- `output_keys` 与 dict 输出 key 完全一致。
- `required_window == window + extra_window`。
- `reset()` 清空状态和输出缓存。
- `meta_info` 包含稳定字段。
- `return_dict`、`g_index`、`outputs` 的行为与 `rIndicator` 保持同一心智模型。
- `rSignal` 不导入 pandas、minbt 或其它应用层依赖。
- orderbook/trade family 不默认维护输入历史窗口。
- 信号实现文件遵守 `<family>/<signal>.py` 结构。
- 顶层导出、family 导出、信号文件导入都可用，例如 `sigma2.rSMA`、`sigma2.kline.rSMA`、`sigma2.kline.sma.rSMA`。
- 通用 pyta2 基类和 resolver 不承载具体信号 catalog；具体 pyta2 快捷信号从 `sigma2.<family>.pyta2` 导出。

## 推荐实施顺序

当前实现顺序应从“最小 core”转为“稳定信号结构”：

1. 保持已实现的 `rSignal.step()`、family 子类和最小示例信号契约不变。
2. 先把当前聚合信号重构为根级 `<family>/<signal>.py`，例如 `kline/sma.py`、`orderbook/book_spread.py`。
3. 将 `rPyta2Signal` 与 `rPyta2SMA` 分层：通用 pyta2 信号基类放入 `core/pyta2.py`，resolver 放入 `utils/pyta2.py`，具体 `rPyta2SMA` 放入 `kline/pyta2/sma.py`。
4. 补齐导入路径 contract tests，确保顶层便捷导出和分组导出都稳定。
5. 更新 README、交接文档和计划索引，移除“优先扩展 pyta2 catalog”的旧表述。
6. 再实现最小 `SignalEngine`，仅作为 core 消费者，不反向污染 core。
7. 再实现 `FeatureSet`、DataFrame batch、minbt adapter。

暂不优先做：

- 全面迁移 pyta2 指标。
- 为所有 pyta2 指标生成 `rPyta2Xxx` 快捷类。
- 复杂 DAG、batch 向量化优化、minbt 深度集成。

最终判断：

```text
core-first:
    rSignal.step -> root family package -> concrete signal files -> core/app consumers

not app-first:
    FeatureSet -> hidden signal objects

not rolling-first:
    rolling/update/forward as parallel user entry points
```

这样 sigma2 可以立刻写、立刻用；用户只有一个入库入口 `step()`，并且未来高层接口变化不会破坏已经写好的信号类。
