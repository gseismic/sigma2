# sigma2 Operator、Signal 与 Outcome 设计

创建时间：2026-10-28 07:03 CST
更新时间：2026-10-28 07:36 CST
状态：确定方案，按 PLAN-027 实施。

## 1. 背景与目标

sigma2 面向 K 线、盘口、成交等市场事件，提供可以逐条推进的计算对象。量化研究与训练系统可以依赖 sigma2 的计算结果，自行决定哪些结果用作特征、目标或其他分析数据。sigma2 的核心概念不依赖训练系统的术语和对象。

本稿依据本次讨论，重新设计核心类与时间契约。希望 sigma2 与 pyta2 的主要区别是：

- sigma2 的 `step()` 每次接收**一个逻辑时点的数据对象**，计算对象自行维护需要的状态或历史。该对象可以承载多个 symbol 的数据，不要求将其字段展开。
- pyta2 的 `rolling()` 接收具体算子要求的历史序列，由调用方准备序列。

除此之外，时间配置、结果位置、schema、输出和缓存语义尽可能与 pyta2 的 `rOperator` 对齐。sigma2 保留市场事件 family、字段绑定和输出身份等自身能力。

本稿在本次讨论后确定，实施过程见 [PLAN-027](../dev/PLAN-027-kline-bundle-operator.md)。最初设计基线为 sigma2 提交 `5903336` 和 pyta2 提交 `cb6e864`；实施期间 pyta2 更新到 `85a2e84` 并统一使用 `result_index`。[单向逐条运行设计](sigma2-20260927-rolling-only.md)记录迁移前的 0.6.0 生命周期。参考的 pyta2 文件为 `pyta2/base/operator.py`、`indicator.py`、`effect.py` 和 `docs/design/rolling-base-20261025-warmup.md`。

## 2. 主要使用场景

| 优先级 | 场景 | 预期用法 |
| --- | --- | --- |
| 高 | 按 K 线逐时点计算均线、RSI 等 | `rKlineSignal.step(bar)` 接收 K 线对象，一次调用推进一个逻辑时点 |
| 高 | 自定义有递推状态的市场信号 | 继承 `rSignal` 或相应 family，自行维护状态并实现 `forward()` |
| 高 | 计算未来 5 个时点的 K 线收益率 | `rKlineOutcome.step(bar)` 接收 K 线对象，等待 5 步后输出对应历史锚点的值 |
| 高 | 按历史锚点批量整理逐条结果 | 普通信号按当前行对齐；Outcome 在成熟后写回所属锚点 |
| 高 | 复用 pyta2 指标 | sigma2 内部将事件整理成子指标所需输入，调用 `rolling()` |
| 中 | 从盘口快照、逐笔成交生成信号 | 每次 `step()` 分别接收完整盘口快照或一笔成交 |
| 中 | 用历史 ATR 和未来行情计算触发情况 | 同时声明锚点前预热和固定未来等待期 |
| 高 | 多 symbol K 线运行 | 一个 `KlineBundle` 包含一个逻辑时点的多 symbol 截面，一个算子可一次计算所有 symbol |
| 中 | 多数据段运行 | 按实际输入序列维护独立状态，序列边界处重置或创建新实例 |

训练层可以使用这些结果，但特征、标签和训练集构造不进入上述核心类。

## 3. 核心类与命名

| pyta2 | sigma2 | 时间语义 | sigma2 的单次输入 |
| --- | --- | --- | --- |
| `rOperator` | `rOperator` | `n_backward >= 0`，`n_forward >= 0` | 一个逻辑时点的数据对象 |
| `rIndicator` | `rSignal` | `n_forward = 0` | 一个逻辑时点的数据对象 |
| `rEffect` | `rOutcome` | `n_forward >= 1` | 一个逻辑时点的数据对象 |

```text
sigma2.rOperator
├── sigma2.rSignal
└── sigma2.rOutcome
```

`rSignal` 表示结果属于当前事件位置。Signal 可以是技术指标、市场结构统计、组合信号或其他当前可计算的值；它不保证用户会进行交易。

`rOutcome` 表示结果以某个位置为锚，需要等待固定数量的后续观测。它不要求关联某个 `rSignal`，不表达因果关系，也不保证结果是实际交易收益。它既可以计算未来收益率、最高价、最低价，也可以计算窗口统计或边界触发结果。

训练中的 `target`、模型预测和数据集概念属于消费层。sigma2 的 Outcome 输出可以被消费层用作训练目标，也可以用于其他分析。

### 3.1 名称比较

| 方案 | 优点 | 代价 | 建议 |
| --- | --- | --- | --- |
| `rResult` | 表达宽泛 | 任意计算都有 result，无法体现后续观测的语义 | 不采用 |
| `rTarget` | 训练用途直观 | 把消费层角色放入核心抽象；目标也不一定依赖未来 | 不采用 |
| `rEffect` | 与 pyta2 同名 | 容易联想到因果影响；sigma2 已选择 `rSignal` 而非 `rIndicator` | 可行 |
| `rOutcome` | 与 `rSignal` 的事件语言相配，不依赖训练概念 | 与 pyta2 的 `rEffect` 名称不同；必须说明不要求 Signal 或交易动作 | 采用 |

### 3.2 对应关系与代码复用

| 方案 | 优点 | 代价 | 建议 |
| --- | --- | --- | --- |
| sigma2 独立实现 `rOperator`，遵守相同契约 | `step()` 的单事件输入清楚，保留现有错误保护 | 需要维护两份生命周期实现 | 本稿采用 |
| sigma2 直接继承 pyta2 `rOperator` | 可复用已有方法 | 会继承 `rolling()`；pyta2 的 runner 也会将该子类视为接收历史序列的算子 | 不采用 |
| 两个库共享中立的生命周期实现 | 长期减少重复，便于行为同步 | 需要先调整 pyta2 内部边界，不能直接依赖不稳定的私有实现 | 后续评估 |

“对应”是公共语义上的对应，不要求 Python 继承关系。sigma2 继续复用 pyta2 的 `Schema`、`Space` 和缓存工具；对两库共有的行为按同一契约维护。

## 4. 时间契约

### 4.1 固定配置

| 属性 | 含义 |
| --- | --- |
| `n_backward` | 结果所属位置之前，完整输出需要的最少前置预热点数，不含该位置自身 |
| `n_forward` | 结果所属位置之后，固定等待的观测数 |
| `min_periods` | `n_backward + 1 + n_forward` |
| `g_index` | 当前已处理的逻辑时点位置；重置后为 `-1` |
| `result_index` | 本次结果所属的位置：`g_index - n_forward` |

两个方向的点数均为非布尔整数，构造后只读。`rSignal` 固定 `n_forward=0`；`rOutcome` 要求 `n_forward>=1`。更换周期或未来期使用新实例，`reset()` 清除状态但不改变配置。

sigma2 使用 `result_index` 表达结果所属位置，避免与训练中的 target 混淆。pyta2 在实施期间通过提交 `85a2e84` 将 `target_index` 改名为 `result_index`，两库现使用相同名称与计算方式。

`min_periods` 是完整输出具备有效计算条件的最少观测数，不保证数据有效，也不表示各字段必须同时开始输出。子类负责根据数据与 schema 返回有效值或缺失值；预热期间基类仍调用计算钩子，以便递推状态和子对象正常推进。

| 计算 | `n_backward` | `n_forward` | `min_periods` | 当前结果位置 |
| --- | ---: | ---: | ---: | --- |
| SMA(10) | 9 | 0 | 10 | `g_index` |
| 未来 5 点收益率 | 0 | 5 | 6 | `g_index - 5` |
| 锚点处需 20 点均值，随后观察 5 点 | 19 | 5 | 25 | `g_index - 5` |

点数以该实例成功的 `step()` 次数计。单 K 线每次接收一根 Bar，Bundle 每次接收一个共同快照；未来 5 点表示后续 5 个输入。自然日、停牌和缺失时点由数据来源或上层处理，缺失 symbol 随共同快照推进，不静默补价格。

### 4.2 固定未来期与结果位置

一个 `rOutcome` 实例的 `n_forward=H` 固定。当前处理位置为 `s` 时，返回值属于 `t=s-H`；当 `t<0` 时还没有可归属的锚点，子类的计算钩子应按 schema 返回缺失值。基类仍调用该钩子以推进状态，不自动屏蔽它的返回值。无论路径中的事件是否提前发生，都在第 `H` 个后续观测到达时返回该锚点的结果，与 pyta2 的固定未来期契约一致。

一个实例的全部输出字段共享该锚点和固定等待期。不同未来期可使用独立实例；若某个组合选择等待最长未来期后一起返回多个字段，须明确所有字段都在那个统一时点输出。

例如收盘价为 `[100, 105, 110, 121]`，未来期为 2：

| `g_index` | 收盘价 | `result_index` | 本次输出 |
| ---: | ---: | ---: | ---: |
| 0 | 100 | -2 | 缺失 |
| 1 | 105 | -1 | 缺失 |
| 2 | 110 | 0 | 0.10 |
| 3 | 121 | 1 | 约 0.152381 |

输出缓存按**产生时间**保留上述四次结果。按锚点整理的等长列是 `[0.10, 0.152381, 缺失, 缺失]`；末尾未成熟的位置不是零收益。

## 5. 构造与逐条接口

共同接口如下，省略类型注解和方法实现：

```python
class rOperator:
    def __init__(
        self, schema, *, n_backward, n_forward,
        buffer_size=1, buffer_factor=2, return_dict=False,
    ): ...

    def step(self, *args, **kwargs): ...
    def reset(self): ...
    def resize_buffer(self, buffer_size): ...
    def forward(self, *args, **kwargs): ...
    def reset_extras(self): ...


class rSignal(rOperator):
    def __init__(self, schema, *, n_backward, **kwargs): ...


class rOutcome(rOperator):
    def __init__(self, schema, *, n_backward, n_forward, **kwargs): ...
```

- `rSignal` 将 `n_forward` 固定为 0；`rOutcome` 校验它至少为 1。`rOperator` 是共同语义基类，具体市场计算优先继承明确的子类。
- 一次成功的 `step()` 在调用计算钩子前将 `g_index` 增加 1。首次成功调用使用索引 0；`forward()` 可读取当前 `g_index` 和 `result_index`。
- `forward()` 是子类计算钩子，可能修改递推状态或推进子对象。业务调用方使用 `step()`，不能把直接调用 `forward()` 当作一次完整推进。
- `reset_extras()` 默认无操作；需要状态或子对象的子类覆盖它。构造期间会调用重置钩子，子类应在调用 `super().__init__()` 前准备好钩子所需的配置和子对象。
- 每个实例维护一条按逻辑时点顺序推进的数据流；一个输入对象可以包含多个 symbol。`g_index` 统计实例的调用步数，不自动成为各 symbol 的独立索引。不保证并发调用和重入安全。已处理数据发生修订时，使用新实例或重置后重放；不恢复 `update_last()`。

`name`、`full_name`、`output_keys`、`schema`、`make_dict_output()` 和 `outputs` 的共同含义与 pyta2 对齐；`meta_info` 使用 `result_index` 并包含共同字段和 sigma2 自身的事件、故障及列身份字段。`full_name` 是子类定义的计算身份；`family` 是 sigma2 的事件输入元信息。当前按 OHLCV 字段声明的 `step_input_keys` 如何适配对象输入和批量处理，见第 6、9 节。

构造参数与 pyta2 一致，移除 sigma2 0.6.0 独有的 `name=` 构造参数；类属性 `name` 和 `full_name` 仍保留。

下面是使用示意：

```python
from sigma2 import rKlineBundleFutureReturn, rKlineBundleMA

signal = rKlineBundleMA(2, symbols=symbols, return_dict=True)
outcome = rKlineBundleFutureReturn(2, symbols=symbols, return_dict=True)

for bundle in ordered_bundles:
    signal_value = signal.step(bundle)      # 属于 signal.result_index
    outcome_value = outcome.step(bundle)    # 属于 outcome.result_index
    if outcome.result_index >= 0:
        print(outcome.result_index, outcome_value)
```

`ordered_bundles` 按时点提供 `KlineBundle`。每个输出字段按固定的 `symbols` 顺序返回各 symbol 的结果；Signal 和 Outcome 是各自独立的计算对象。K 线 schema 与 symbol 轴的关系见专题设计。

## 6. 事件 family 与窗口

输入 family 和时间语义是两个维度。K 线、盘口和成交分别规定一条事件包含什么字段；Signal 与 Outcome 决定结果在何时所属和何时成熟。

K 线 family 建议以可复用的内部输入实现分别组合两种时间类型：

```text
rKlineSignal       = K 线输入 + rSignal
rKlineOutcome      = K 线输入 + rOutcome
rKlineWindowSignal = K 线输入窗口 + rKlineSignal
rKlineWindowOutcome = K 线输入窗口 + rKlineOutcome
rKlineBundleSignal = K 线截面输入 + rSignal
rKlineBundleOutcome = K 线截面输入 + rOutcome
```

以上表示职责组合，不限定必须采用多重继承。单 K 线 family 接收 `KlineBar`，Bundle family 接收 `KlineBundle`；两者均以一个对象传入 `step()`。盘口和成交保留各自输入签名；出现对应 Outcome 的真实需求时，可复用相同的 family 输入契约。

0.6.0 的未来计算经由 `rKlineWindowSignal` 继承 `rSignal`。迁移后共享 K 线输入及窗口能力，未来计算属于 `rOutcome`，遵守 `rSignal` 的零未来期约束。

自有递推算法可以只保存状态。需要历史数组的算法可以在内部维护窗口；`history_window` 描述实际保留量，`min_periods` 描述预热和等待要求，二者不能一概视为同一含义。具体算法或适配器应明确自己需要的历史范围，不能仅凭 `min_periods` 推断任意 pyta2 算子的完整输入需求。

### 6.1 KlineBundle 的设计边界

`KlineBundle` 表示同一时点的多 symbol 快照，一次 `step(bundle)` 推进一个共同快照。固定顺序的 `symbols` 构成输出轴；某个 symbol 缺失仍推进共同时间，但不自动补价格。未来结果的每个 symbol 共用 `result_index` 指向的锚点。排名、相对强度和其他横截面信号一次处理整个 Bundle。单 K 线计算位于 `sigma2.kline`，横截面计算位于并列的 `sigma2.kline_bundle`，已有单 K 线算子可通过映射适配器复用。

快照字段、时间与缺失表示、结果的 symbol 轴和缓存细节见 [KlineBundle 横截面设计](kline-bundle-20261028-overview.md)。

## 7. Schema、输出与缓存

### 7.1 Schema 与缺失值

schema 的构造、标准化、校验和输出处理与当前 pyta2 保持一致，直接使用同一套 `Schema` 和 `Space`：

1. 接受 `Schema` 实例、`list[(字段名, Space)]` 或 `Mapping[字段名, Space]`；列表或 mapping 用 pyta2 的 `Schema` 构造，已有 `Schema` 直接使用。
2. 沿用 pyta2 对非空字段、字段名类型、重复字段和 `Space` 类型的校验及字段顺序；不在 sigma2 再定义不同的 schema 标准。
3. `schema`、`output_keys`、`schema.get_dtypes()`、`make_dict_output()`、`return_dict` 和 `missing_output` 与 pyta2 同义；`missing_output` 依据各字段 `Space.null_value`，单字段返回单值，多字段返回按顺序排列的 tuple。
4. 不在 sigma2 单独引入 dtype 简写、不同的形状限制或新的 schema 自动校验。若以后需要扩展，先统一 pyta2 的相关契约再同步两边。

| 方案 | 优点 | 代价 | 建议 |
| --- | --- | --- | --- |
| 直接使用 pyta2 的 `Schema` 与 `Space` | 构造、校验和缺失值契约一致 | 现有纯 dtype 声明需要迁移 | 本稿采用 |
| 仅在 sigma2 保留 dtype 简写 | 简单公式书写较短 | 增加双方输入及缺失语义差异 | 不采用 |
| 保留当前 `_DTypeSchema` | 当前自定义 Signal 无需修改 | dtype 字段缺少 `Space.null_value`，不能统一 `missing_output` | 不采用 |

`step()` 的输出转换沿用 pyta2 的 `rolling()`：需要缓存或字典输出时使用 `make_dict_output()` 转换字段；`return_dict=False` 始终返回 `forward()` 的原始值，`return_dict=True` 返回转换后的 mapping。关闭缓存且 `return_dict=False` 时不额外执行字段转换。Bundle 横截面 schema 的每个 Space 描述一个 symbol 的值，family 增加 symbol 轴；缓存展开为 pyta2 标量列并重新组装。sigma2 不在 schema 层单独强制检查输出值；例如把 `1.5` 声明为整数输出时，原始返回值与按 dtype 存储的值可能不同。

当前 pyta2 的 schema 与底层表工具对缺失值和形状的支持存在边界：例如 `Bool` 的默认 `null_value` 为 `None`，但 `DequeTable` 将布尔 dtype 的 `None` 写成 `False`。Bundle 逐元素展开缓存，可以保留多维 Space 的 symbol 轴及元素形状；普通 pyta2 表不能直接缓存数组字段。本稿不保证所有 dtype 的缺失值可以无损保存；需要可靠区分缺失值时，调用方应选择可表示缺失哨兵的空间，或在两库共同设计掩码等方案。

### 7.2 返回值与缓存

- `return_dict=False` 返回 `forward()` 的原始标量、多输出序列或 mapping；`return_dict=True` 按 `output_keys` 返回 mapping。
- 缓存默认 `buffer_size=1`；`0` 或 `None` 关闭，`-1` 无限，正整数保留最近 N 条。参数语义与 pyta2 一致；无限缓存必须由调用方显式选择。
- 缓存按调用成功顺序保存，即 Outcome 缓存反映产生时间，不自动回填历史锚点。关闭缓存时 `outputs` 和 sigma2 的便捷属性 `latest` 为 `None`。
- `resize_buffer()` 负责切换或调整输出缓存，不改变算法所需的输入历史。缩小容量保留最新结果；关闭后再次开启从空缓存开始。
- `latest` 是 sigma2 保留的便捷属性，并不改变 pyta2 的输出含义。`rSignal.factor_names` 暂保留现有列身份：单输出使用 `full_name`，多输出使用 `full_name.output_key`。Outcome 的批量列采用同一身份生成规则，但不要求将其命名为 factor。

## 8. 状态、失败与重置

正常运行时，一个成功的 `step()` 推进一次索引并生成一次结果；`reset()` 重置索引、缓存及子类和子对象状态，保留固定配置。

计算、输出转换或缓存写入发生异常时，本稿建议保留 sigma2 现有的故障保护：

1. `g_index` 恢复到上一次成功处理的位置，实例进入 faulted 状态。
2. 失败时子类状态或缓存可能已经部分改变；故障期间的运行态不作为可信计算结果，后续 `step()` 必须拒绝。
3. `reset()` 必须在所有重置钩子成功后才解除 faulted；重置失败时保持 faulted。恢复后从已确认输入序列开头重放。

这与本地 pyta2 当前实现有明确差异：pyta2 的 `rolling()` 在调用 `forward()` 前推进索引，没有同等故障锁定。两库共同采用何种错误契约需要单独协调；在 pyta2 未调整前，本稿不把两者描述为已经完全一致。保持该保护是因为事件输入和递推状态一旦部分推进，直接继续会让后续结果不可信。

## 9. 批量重放与输出对齐

两种批量计算都创建新的计算对象，按逻辑时点顺序调用它的 `step()`；不维护第二套公式。单 K 线输入为 `KlineBar` 序列，Bundle 输入为 `KlineBundle` 序列，结果按时间和 symbol 对齐；其他 family 保留其各自事件输入方式。

| 接口 | 接收对象 | 输出行的含义 |
| --- | --- | --- |
| `forward_signal_apply()` | `rSignal` 子类 | 输出对齐当前逻辑时点；`result_index == g_index` |
| `forward_outcome_apply()` | `rOutcome` 子类 | 成熟结果写到 `result_index`，末尾未成熟位置按字段缺失值填充 |

`forward_outcome_apply()` 按每次 `step()` 后的 `result_index` 放置结果：负索引不写入，非负索引写入对应锚点。对单一逻辑输入序列，输出与输入步数等长；空输入返回对应 schema 的空列，输入长度不超过 `n_forward` 时全部锚点都未成熟。预热不足或输入无效的字段使用算法返回的缺失值，不能只凭 `result_index>=0` 推断数值有效。批量结果按 schema dtype 转换为 NumPy 数组；其 dtype 与缺失表示限制见第 7 节。

逐条 Outcome 与按锚点回填的 batch 在同一锚点比较；逐条缓存与 batch 列的行号不同。对于按 schema 存储时不改变的数值，两者应一致；原始返回值与 dtype 存储值可能因转换不同。若消费层需要按产生时间记录，直接消费 `step()` 或其输出缓存。多 symbol 结果共享快照锚点并按固定 symbol 轴回填。

## 10. 与 pyta2 组合及资源边界

sigma2 原生算法可以使用有界状态，也可以在内部组合 pyta2 指标。需要 pyta2 指标时，sigma2 将单条事件加入所需历史，再按子指标契约传入 `rolling()`；`reset()` 时一起重置子对象。不得因为父类是 `step()` 就把单个价格误传给需要序列的指标。

并非所有 pyta2 算子都能接受最近 N 点代替完整前缀：部分未来期实现检查输入长度是否为 `g_index+1`，并按绝对位置访问。以下方案各有边界：

| 方案 | 优点 | 代价 |
| --- | --- | --- |
| 使用已验证可接受有限窗口的算子 | 状态有界，适合长期事件流 | 只能用于已确认输入契约的具体算子 |
| 为要求前缀的算子保存或提供完整前缀 | 遵守原算子的位置语义 | 历史存储随流长度增长，需要明确资源所有权 |
| 与 pyta2 协商支持带位置的有界窗口 | 可以兼顾通用复用和有界内存 | 需要修改并验证上游契约，不能由 sigma2 单方面假设 |

本稿采用按具体算子验证输入契约的原则。默认不静默保存无限输入历史；无法用有限窗口正确适配时，应明确要求完整历史来源或拒绝该适配。不能仅将当前 Outcome 的 `backward()` 改名为 `rolling()`，再继续传同一个有界窗口。

选定的 pyta2 提交中基类、均线族及部分普通指标已迁移到新时间契约，其他指标和具体 effect 仍在迁移；其版本号仍为 `0.0.1`。sigma2 的桥接使用新时间属性并要求通用适配器显式给出历史长度；尚未迁移的 ATR、KDJ 及未来路径计算以有界状态实现。两库的位置属性均为 `result_index`。具体支持的提交及依赖约束见 PLAN-027。

## 11. 现有接口的迁移影响

以下是相对 `0.6.0` 的不兼容或可观察变化，已按 PLAN-027 处理：

1. 新增共同的 `rOperator` 与 `rOutcome`；`rSignal` 改为固定零未来期。现有未来计算从 Signal 层迁到 Outcome 层。
2. 用 `n_backward`、`n_forward`、`min_periods`、`result_index` 取代 `window`、`extra_window`、`required_window` 和 `set_window()`。具体类的算法周期仍可使用 `n` 等业务参数；上游也已采用 `result_index`。
3. 输出缓存默认从无限改为 1；`None` 改为关闭，`-1` 显式无限，`0` 改为关闭。调用方依赖现有无限默认时必须迁移。
4. 普通 dtype 简写改为完整 `Space` 声明；本稿建议移除当前构造参数 `name=`。`factor_names` 对现有 Signal 保留。
5. `sigma2.kline.target` 下的未来计算迁往 `sigma2.kline.outcome`；例如 `rKlineFutureReturn` 保留业务名称。旧路径不提供转发。
6. 未来收益类的 `horizon` 统一为 `n_forward`，位置参数仍可用于简短调用。旧 keyword 调用需要迁移。
7. K 线 `step()` 从展开 OHLCV 字段改为接收 `KlineBar`；Bundle family 接收 `KlineBundle`，旧调用方及其 batch 的字段提取方式需要迁移。
8. `forward_signal_apply()` 收窄到 `rSignal`；未来结果改用 `forward_outcome_apply()`，按锚点回填。`meta_info` 增加时间字段并删除旧窗口字段，多 symbol 输入及返回结构依赖 `KlineBundle` 设计。
9. 更新 README、示例、扩展指南、导出及使用方；不把历史交接和旧计划中的过时结论当作当前代码状态。

版本升至 `0.7.0`，不为上述旧接口提供兼容层；实施记录和验证范围见 PLAN-027。

## 12. 三轮查漏补缺

### 第一轮：调用者与命名

- 普通使用者用 `step(bar)` 输入 K 线对象，无需展开字段；复杂子类才需要接触窗口和子指标。
- `rSignal` 与 `rOutcome` 都可以独立计算；不会要求传入训练目标、模型或另一个 Signal。
- `rOutcome` 明确仅表示固定正未来期，避免将 `rResult` 扩展成任何计算输出。
- K 线输入结构与结果的时间类型分离，避免未来结果被迫继承零未来期的 `rKlineSignal`。

### 第二轮：时间、缺失与 batch

- `result_index` 在结果成熟前可能为负；它为非负也不保证预热或数据有效。
- `min_periods` 不阻止提前输出部分有效字段；各字段的缺失值与 schema 一致。
- 一个 Outcome 的多个字段共享同一锚点和固定未来期；不同未来期使用独立实例或显式等待最长未来期。
- 空输入、输入少于未来期和尾部未成熟位置有明确输出位置；不同 dtype 的缺失值遵循 pyta2 的 schema 与表工具能力。多 symbol 形状按 [KlineBundle 横截面设计](kline-bundle-20261028-overview.md) 定义。
- `step()` 按产生时间返回，batch 按锚点回填；消费层如基于时间截断数据，还需自行确认结果的实际可用时间。

### 第三轮：状态、资源与演进

- `reset()` 失败时继续故障锁定；子指标与父对象一起重置和重放。
- 默认输出缓存有界；输入历史与输出缓存分开配置，不能由 `min_periods` 自动推导任意算子的保留量。
- pyta2 的完整前缀要求不能由有限窗口无条件满足；适配器须声明资源及兼容边界。
- 现有 pyta2 的失败保护及未迁移组件与本稿尚有差异；schema 处理按 pyta2 对齐，但部分 dtype 的缺失值能力本身有限，不能误称这些限制已解决。
- sigma2 与 pyta2 都使用 `result_index` 表达通用结果位置；训练角色、数据集切分和模型预测都留在消费层。

## 13. 评审重点

1. `rOperator / rSignal / rOutcome` 的名称和固定时间约束是否符合预期。
2. 两库的 `result_index` 和时间属性保持一致。
3. schema 完全采用 pyta2 的处理方式；是否移除现有 `name=` 构造参数。
4. 故障保护、缓存与 pyta2 表工具目前的缺失值边界是否接受。
5. `KlineBundle` 一步输入的具体含义、多 symbol 的状态和输出对齐；Outcome batch 按锚点回填的边界。
6. pyta2 有界窗口/完整前缀的适配边界是否合适。
