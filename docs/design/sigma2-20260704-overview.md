# sigma2 总体设计

更新时间：2026-07-07 12:26 CST

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
- `FeatureSet`、DataFrame batch、ML 矩阵生成、minbt adapter、因子分析、深度学习数据集和强化学习环境都是应用层能力，应该消费 core，而不是定义 core。
- 面向真实研究训练场景，应用层中心不应是传统 `FactorAnalysis`，而应是更通用的 `FeatureData -> TargetData -> ResearchDataset -> AnalysisReport / EnvBuilder`。
- IC、RankIC、分组收益和换手分析是特征诊断能力，不是 sigma2 core，也不是研究训练层的唯一中心。
- 研究训练层可以先作为 `sigma2.research` 存在，但接口必须按未来可拆成独立包 `sigma2-research` 的边界设计。

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
| 研究训练层 | `sigma2.research.*` 或后续独立包 `sigma2-research` | 最后稳定 | 特征生成、标签生成、因子诊断、监督学习数据集、强化学习环境、minbt bridge |

稳定性顺序：

1. 先稳定核心层。
2. 再稳定常用内置信号。
3. 再稳定 pyta2 信号基类和 resolver。
4. 最后稳定 `sigma2.research` 等研究训练层门面。

原因：应用层需求最容易随真实使用变化，核心信号继承契约一旦稳定，用户今天写的信号就能被未来任意应用层复用。

## 整体源码结构

sigma2 的源码树应直接表达用户心智：打开包根目录，首先看到的是可以使用和扩展的信号分类。非信号对象不能挤占根目录的主要位置，应优先放入 `core/`、`utils/` 或明确的应用层命名空间。

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
  research/        # 后续可选；按未来独立包边界设计
```

稳定规则：

- `sigma2.<family>` 是具体信号的主发现入口。
- 根目录下的业务命名目录优先留给信号输入类型分类，例如 `kline`、`orderbook`、`trade`、未来的 `funding_rate`、`news`。
- `research` 是明确的应用层命名空间，不是信号 family；如果后续拆成独立包，sigma2 core 和信号目录不应受影响。
- 每个具体信号一个文件；文件内只放该信号及其非常小的私有辅助逻辑。
- 各级 `__init__.py` 只负责导出，不承载具体信号实现。
- 顶层 `sigma2.__init__` 可以 re-export 常用信号，但顶层导出不是源码组织依据。
- 文件名使用小写语义名，类名使用 `rXxx`，保持与 `pyta2.base.rIndicator` 的 rolling 类心智一致。
- Python 关键字冲突用后缀处理，例如 `return_.py` 中定义 `rReturn`。
- 新增输入数据类型时新增根级 family 目录和对应 family 基类，不修改已有 family 的输入契约。
- 新增具体 pyta2 快捷信号时放在所属数据类型目录下，例如 K 线 pyta2 SMA 位于 `kline/pyta2/sma.py`。
- `core/` 是唯一核心目录，放稳定基类和输入契约，例如 `rSignal`、`rKlineSignal`、`rOrderBookSignal`、`rTradeSignal`、`rPyta2Signal`；不放因子分析、训练数据集、minbt adapter 或 RL 环境。
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
- 上层 signal runner、`make_features()`、`ResearchDataset`、minbt bridge 都能消费同一个信号对象。
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
- signal runner
- `make_features()`
- `ResearchDataset`
- minbt bridge
- ML / DL batch runner

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

## 研究训练层

sigma2 的长期目标不是只做传统技术指标，也不是只做传统因子分析，而是支持真实量化研究和训练闭环：

```text
market data -> rSignal -> FeatureData -> TargetData -> ResearchDataset -> model / report / env
```

因此研究训练层的中心应是通用特征和训练数据，而不是 `FeatureSet` 或 `FactorAnalysis`。

关键判断：

- `Signal` 是 sigma2 core 中的 `rSignal` 对象，负责把原始行情流转成信号输出。
- `Feature` 是模型输入，可以来自 sigma2 signal，也可以来自外部表、embedding、基本面、新闻或人工特征。
- `Factor` 是有金融解释意义、常用于横截面 IC 和分组收益诊断的一类 feature。
- IC、RankIC、QuantileReturn、Turnover 是分析器，不是 core signal。
- 深度学习训练需要 `Dataset`、`Split`、`Transform` 和 tensor 输出。
- 强化学习训练需要 `Observation`、`Action`、`Reward`、`Simulator` 和 `Env`，不能用 IC 分析模型替代。

推荐位置：

```text
sigma2/research/
```

但边界按未来独立包设计：

```text
sigma2-research
```

设计约束：

- `sigma2.research` 只依赖 sigma2 的公共信号协议，不依赖 `sigma2.core` 的内部状态实现。
- `sigma2.research` 可以消费外部 feature，不要求所有 feature 都来自 `rSignal`。
- `sigma2.core` 不导入 `research`，不理解 IC、label、dataset、env、minbt。
- 将来拆包时，用户代码应主要改 import，不应重写信号或训练流程。

### 研究训练层模块结构

目标结构：

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

- `feature`：从 sigma2 signal 或外部数据生成、对齐、转换、存储 `FeatureData`。
- `target`：生成监督学习标签，例如未来收益、分类标签、风险目标。
- `analysis`：做特征诊断，例如 IC、RankIC、分组收益、换手、冗余、泄漏检查、分布漂移。
- `dataset`：生成深度学习和传统机器学习训练数据，处理 split、mask、sample weight、tensor 形态。
- `rl`：构建强化学习 observation、action、reward、env 和 offline trajectory。
- `bridge`：连接 sigma2 signal 和 minbt 等外部框架，但不污染 core。

### SignalLike 协议

研究训练层不应要求输入对象一定是 `rSignal` 子类。它只需要一个最小协议：

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
- 外部特征生成器也可以实现该协议进入研究训练层。
- 研究训练层只能调用 `reset()` 和 `step()`，不能调用 `forward()`。
- 多 symbol、多 venue、多数据源由 runner 为每条输入流创建独立 signal 实例或 clone。

### FeatureData

`FeatureData` 是研究训练层的核心数据对象。它表达模型输入，不等同于传统因子。

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

推荐用户入口不强制用户显式构造 `FeatureData`：

```python
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

多 family 输入：

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

- 普通用户传 `data`、`signals`、`time`、`symbol` 即可，不应被迫理解 `KlineInput`、`OrderBookInput` 等重对象。
- 内部可以有 normalizer、schema、runner、registry，但这些不进入简单主路径。
- `FeatureData` 不应锁死 pandas；可以有 DataFrame、numpy、arrow、polars、torch 等后端适配。
- `mask` 是一等公民。停牌、缺失、涨跌停、不可交易、无标签、warmup 都应通过 mask 或 metadata 表达，而不是简单丢行后破坏 `[time, symbol]` 结构。
- `feature name` 必须可追溯到 `signal.family`、`signal.full_name`、`output_key` 和可选版本。

### TargetData

`TargetData` 表达监督学习标签。它必须显式解决未来函数问题。

典型入口：

```python
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
- `start`：收益从何时开始计算，默认应是 `next`，避免默认未来函数。
- `return_type`：`simple` 或 `log`。
- `align`：target 如何与 feature 的时间戳对齐。

扩展目标：

- `ForwardReturn`：K 线未来收益。
- `ForwardMidReturn`：订单簿中间价未来收益。
- `ClassificationTarget`：涨跌、分位数或事件分类标签。
- `RiskTarget`：未来波动率、回撤、尾部风险。

约束：

- 标签生成不进入 `rSignal`。
- `TargetData` 必须记录 horizon、start、price、return_type 等 metadata，保证训练结果可追溯。
- 多 horizon target 可以生成多个 target column，但必须保留 horizon metadata。

### AnalysisReport

分析模块负责诊断 feature 是否有预测信息、是否稳定、是否冗余、是否存在明显泄漏。

用户入口：

```python
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
```

第一批分析器：

- `IC`：Pearson IC。
- `RankIC` 或 `IC(method="spearman")`：Spearman 秩 IC。
- `ICDecay`：不同 horizon 下的信息衰减。
- `QuantileReturn`：分组收益和单调性。
- `LongShortReturn`：top-bottom 或 top-minus-bottom 收益。
- `Turnover`：分位数组合或信号 rank 换手。
- `Correlation`：feature 冗余和共线性。
- `MissingReport`：缺失率、warmup 缺失、symbol 覆盖率。
- `LeakageCheck`：潜在未来函数检查。
- `DriftReport`：训练集、验证集、测试集分布漂移。

IC 默认语义：

- 默认 `axis="cross_section"`，即同一时间截面对多个 symbol 计算相关性。
- 单 symbol 或低 symbol 数场景必须显式使用 `axis="time_series"`。
- `min_count` 控制每个截面最少样本数。
- 支持 `weights`、`groups`、`neutralize`。
- 多日 forward return 的 t-stat 后续应支持 Newey-West / HAC，不能只用普通独立样本假设。

`AnalysisReport` 输出：

```text
AnalysisReport
  tables
  summaries
  diagnostics
  optional plot data
  metadata
```

约束：

- 第一版不应先做复杂图表和 HTML 报告。
- 报告对象优先返回结构化表格和 summary。
- 文件写入、图片生成、HTML 导出必须显式调用，不能在 `analyze_features()` 默认产生外部副作用。

### ResearchDataset

`ResearchDataset` 是深度学习和传统机器学习训练的主对象。

用户入口：

```python
dataset = make_dataset(
    features=features,
    target=target,
    transforms=[
        Winsorize(3.0),
        ZScore(scope="cross_section"),
    ],
    split=WalkForwardSplit(train="3y", valid="6m"),
)
```

也可以从原始数据和 signal 一步构造：

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

核心能力：

- `to_tabular()`：输出 `[sample, feature]`。
- `to_sequence(lookback=60)`：输出 `[sample, lookback, feature]`。
- `to_cross_section(lookback=20)`：输出 `[time, symbol, lookback, feature]` 或等价稀疏结构。
- `to_numpy(kind=...)`：输出 numpy。
- `to_torch(kind=...)`：输出 PyTorch Dataset 或张量适配对象。
- `analyze(...)`：对 dataset 内 features 和 target 做诊断。

关键约束：

- 默认 split 必须是时间序列友好的，例如 walk-forward；不能默认随机切分。
- transform 必须区分 `fit()` 和 `transform()`。标准化、去极值、中性化只能在训练集 fit，再应用到验证集和测试集。
- split、transform、target 必须一起防止未来函数。
- `sample_weight`、`mask`、`groups`、`universe` 都应是 dataset 的一部分。
- `ResearchDataset` 不应要求用户必须安装 torch；torch adapter 应是可选能力。

推荐 tensor 形态：

```text
tabular:
  X: [sample, feature]
  y: [sample]
  sample_weight: [sample]

sequence:
  X: [sample, lookback, feature]
  y: [sample]
  mask: [sample, lookback]

cross_section:
  X: [time, symbol, feature]
  y: [time, symbol]
  mask: [time, symbol]

cross_section_sequence:
  X: [time, symbol, lookback, feature]
  y: [time, symbol]
  mask: [time, symbol, lookback]
```

### FeaturePipeline 与 online 推理

训练和上线必须使用同一套 feature 与 transform 定义，否则离线和在线会漂移。

推荐形态：

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

约束：

- `FeaturePipeline.fit_transform()` 可以生成研究数据。
- `FeaturePipeline.to_online()` 只能使用训练期 fit 好的 transform 状态。
- online runner 只能调用 signal 的 `step()`，不能调用 `forward()`。
- online 输出应能复用训练时的 feature column 顺序、normalizer、mask 策略和 metadata。

`FeatureSet` 可以作为 `FeaturePipeline` 内部或便捷别名存在，但不应成为 core 对象，也不应定义 `rSignal`。

### 强化学习接口

强化学习不是 IC 分析的扩展，而是单独的训练环境问题。

RL 需要的对象：

```text
observation = 市场特征 + 当前持仓 + 现金 + 风险状态
action = 目标权重 / 买卖方向 / order intent
reward = pnl - cost - risk_penalty
simulator = 执行、撮合、费用、滑点、持仓
env = observation/action/reward/simulator 的组合
```

推荐入口：

```python
env = make_env(
    dataset=dataset,
    simulator=simulator,
    observation=PortfolioObservation(lookback=60),
    action=TargetWeight(max_abs=1.0),
    reward=NetReturn(cost=True, risk_penalty=0.1),
)
```

约束：

- `simulator` 是协议，不是硬编码 minbt。
- minbt 可以作为一个 simulator 实现或 bridge。
- `research.rl` 不应自己重写 broker、撮合、订单和账户系统。
- offline RL 需要 `TrajectoryData`，记录 observation、action、reward、done、info。
- reward 必须明确是否扣费、是否考虑滑点、是否有风险惩罚。
- action space 必须显式，例如目标权重、离散买卖、订单意图，不能用含糊字符串隐藏交易语义。

### minbt bridge

minbt 是回测和交易执行框架，sigma2 是信号层，research 是训练和诊断层。

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

或未来独立包：

```python
from sigma2_research.bridge.minbt import MinbtSimulator
```

禁止：

- `rSignal`、family 子类、research 主流程中出现 `update_minbt_bars(...)` 这类外部框架命名。
- 在 sigma2 core 中出现 `Broker`、下单、持仓、资金管理概念。
- 为兼容 minbt 把 sigma2 的 K 线统一叫 `bar`。sigma2 内部仍应使用具体输入类型，例如 `kline`。

### 数据输入与 family 扩展

研究训练层应延续“输入类型决定 family”的原则，但不把重输入对象暴露给简单用户。

用户简单路径：

```python
make_features(data=klines, signals=[...], time="dt", symbol="symbol")
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

- 新数据类型通过新增 family、normalizer、runner 进入应用层。
- 不修改已有 `kline`、`orderbook`、`trade` 输入契约。
- 普通用户不需要显式创建 `KlineInput`；高级用户可以通过 schema/normalizer 控制字段映射。
- `FamilyRegistry` 是 research runner 的扩展机制，不是 `rSignal` core 的父抽象。

### 第一阶段研究训练 API

第一阶段优先稳定这些用户 API：

```python
features = make_features(
    data=klines,
    signals=[rSMA(20), rReturn(5)],
    time="dt",
    symbol="symbol",
)

target = ForwardReturn(horizon=5, price="close", start="next")

report = analyze_features(
    features=features,
    target=target,
    analyses=["ic", "rank_ic", "quantile"],
)

dataset = make_dataset(
    features=features,
    target=target,
    split=WalkForwardSplit(train="3y", valid="6m"),
)

seq = dataset.to_sequence(lookback=60)
```

第一阶段内部对象：

- `FeatureData`
- `TargetData`
- `ResearchDataset`
- `AnalysisReport`
- `WalkForwardSplit`
- `Winsorize`
- `ZScore`
- `ForwardReturn`
- `IC`
- `QuantileReturn`

第一阶段暂不做：

- 完整 RL 环境。
- 完整 minbt 深度集成。
- 自动模型训练框架。
- 大而全 HTML 报告。
- 复杂 DAG 和分布式计算。
- 全量 pyta2 catalog 迁移。

## 版本与兼容性

在 v0 阶段也要人为维持兼容规则。

推荐版本规划：

| 版本 | 冻结内容 |
| --- | --- |
| `0.1.x` | `rSignal.step()`、`rKlineSignal`、`rKlineWindowSignal`、schema/output、基础 K 线自定义信号 |
| `0.2.x` | pyta2 信号基类、常用 K 线内置信号、最小 signal runner |
| `0.3.x` | `rOrderBookSignal`、`rTradeSignal` 的真实信号和 contract tests |
| `0.4.x` | `FeatureData`、`ForwardReturn`、`analyze_features()`、IC / RankIC / QuantileReturn |
| `0.5.x` | `ResearchDataset`、walk-forward split、transform fit/transform、tabular/sequence 输出 |
| `0.6.x` | 初步 RL env builder、minbt bridge、offline trajectory |
| `1.0.0` | 对 core、常用内置信号和研究训练层主路径做正式语义化版本承诺 |

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
- `make_features()`、signal runner 和后续 batch replay 只能调用 `step()`，不能调用 `forward()`。
- `FeatureData` 必须保留 feature columns、time、symbol、mask 和 metadata 的可追溯契约。
- `ForwardReturn(start="next")` 默认不产生当前收盘到未来收盘的隐式未来函数。
- transform 必须有 `fit()` / `transform()` 生命周期，验证集和测试集不能重新 fit。
- `WalkForwardSplit` 或等价时间序列 split 不能泄漏未来数据。
- `ResearchDataset.to_sequence()` 的 feature 顺序、lookback 对齐和 mask 输出稳定。
- analysis 默认无文件写入副作用；导出报告必须显式调用。
- `make_env()` 依赖 simulator 协议，不直接依赖 minbt。
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

当前实现顺序应从“稳定信号结构”转为“研究训练最小闭环”：

1. 保持已实现的 `rSignal.step()`、family 子类、根级信号目录和最小示例信号契约不变。
2. 实现最小 signal runner / `make_features()`，只消费 `SignalLike.reset()` 和 `SignalLike.step()`。
3. 实现 `FeatureData`，先支持 DataFrame 输入输出，但内部契约不要锁死 pandas。
4. 实现 `ForwardReturn` 和 `TargetData`，默认 `start="next"` 并记录 label metadata。
5. 实现 `IC`、`RankIC`、`QuantileReturn` 和 `AnalysisReport`，优先返回结构化表格。
6. 实现 `WalkForwardSplit`、`Winsorize`、`ZScore` 和 `ResearchDataset.to_tabular()` / `to_sequence()`。
7. 在上述闭环稳定后，再实现 `FeaturePipeline.to_online()`，确保离线训练和在线推理复用同一套 feature 顺序和 transform 状态。
8. 最后再做 RL env builder、minbt bridge、torch adapter 和更复杂报告。

暂不优先做：

- 全面迁移 pyta2 指标。
- 为所有 pyta2 指标生成 `rPyta2Xxx` 快捷类。
- 复杂 DAG、batch 向量化优化、minbt 深度集成。
- 自动模型训练框架。
- 完整 gymnasium 兼容层。
- HTML 报告和图表渲染系统。

最终判断：

```text
core-first:
    rSignal.step -> root family package -> concrete signal files -> research consumers

not app-first:
    FeatureSet/FactorAnalysis -> hidden signal objects

not rolling-first:
    rolling/update/forward as parallel user entry points

research-first, but not core-polluting:
    FeatureData -> TargetData -> ResearchDataset -> AnalysisReport / EnvBuilder
```

这样 sigma2 可以立刻写、立刻用；用户只有一个入库入口 `step()`，并且未来高层接口变化不会破坏已经写好的信号类。
