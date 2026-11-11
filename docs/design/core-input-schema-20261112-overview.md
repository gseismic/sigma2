# core 职责、输出契约与输入 schema 设计

- 创建日期：2026-11-12
- 状态：已实施，详见 `docs/dev/PLAN-055-input-schema-OUTCOME.md` 和 `docs/dev/PLAN-056-core-output-contract-OUTCOME.md`。文中“拟议”及“尚未实施”保留设计提出时的语境。
- 更新：第 7 节的输入声明格式和递归校验已由 [简化输入描述声明](input-schema-simple-20261112-overview.md) 替代。
- 依据：工作区 `GOAL.md`、`api-design-zh`、当前 HEAD `1cc2460` 的 core 与输入基类，以及本轮用户对 Bundle 格式和数据粒度的澄清。
- 配套设计：[多 symbol Bundle](bundle-20261111-overview.md)。
- 适用边界：本文件提出下一阶段的优化；当前生命周期仍以 [单向推进设计](operator-single-pass-20261031-overview.md) 和现有代码为准。

## 1. 审查结论与目标

core 不需要整体重写。当前 `rOperator -> rSignal / rOutcome` 已经把计算生命周期和数据输入分开：数据包负责 `step()` 签名和转发，core 负责索引、调用 `forward()`、输出检查、缓存和失败锁定。该方向符合 GOAL 中按数据类型分包的目标。

本轮建议只做三类改进：

1. 将类级输入描述做成无运行副作用的独立模块，`rOperator` 只提供查询入口。
2. 明确输出配置的只读约定与共同存储规则，减少在线缓存和批量输出对配置的不同解释。
3. 补齐输入借用、输出发布、错误边界和扩展方式的契约。

不引入统一行情对象、事件总线、观察者系统、通用计算图、输入校验引擎、每 symbol 调度器或新的状态回滚机制。

## 2. 使用场景与优先级

| 场景 | 频次 | 需要的公共接口 | 不需要暴露的实现 |
| --- | --- | --- | --- |
| 调用已有 K 线指标 | 最高 | 原有构造参数和 `step()` | schema 解析、缓存 dtype 规划。 |
| 自定义已有数据类型 Signal | 高 | 继承对应基类、实现 `forward()` | 核心索引推进与锁定逻辑。 |
| 批量重放相同算法 | 高 | `forward_step_apply()` | 另一套向量化公式。 |
| 自定义固定延迟 Outcome | 中 | 同类数据入口、`n_forward`、`result_index` | 通用事件时间调度器。 |
| 查询输入字段与类型 | 中 | `SomeClass.input_schema()` | 创建算子实例或消费样本。 |
| 定义新数据类型入口 | 中 | 薄 `step()`、输入描述、Signal/Outcome 基类 | 自动识别数据来源。 |
| 指定输出缓存和缺失哨兵 | 中 | 现有 `schema`、`buffer_size` | 存储后端抽象层。 |
| 诊断错误和重新计算 | 中 | 原始异常、失败后新建并重放 | 自动恢复或隐式重试。 |

用户接口应保持调用短、概念少；内部接口应确定类型、状态、所有权和复杂度。输入描述不是调用前置步骤。

## 3. 当前 core 的逐项审查

以下为源码审阅结论，没有运行时验证。pyta2 的行为参考了工作区源码，实施时仍应核对实际依赖版本。

| 对象 | 当前情况与依据 | 判断和建议 |
| --- | --- | --- |
| `rOperator.step` | [operator.py](../../sigma2/core/operator.py) 在计算前标记失败、推进索引，计算和缓存全部成功后才解除 | 主流程正确，保留。无须恢复旧检查点和 reset。 |
| `rSignal` / `rOutcome` | 分别固定 `n_forward=0` 和要求正整数未来步数 | 语义不同，保留两个类；少量参数转发重复无需抽象。 |
| 数据类型入口 | K 线已有共享输入层；盘口、成交和 K 线截面仍有平铺基类 | 目录整理发生在数据包，不把市场字段搬进 core。 |
| 输入描述 | 目前不存在 `input_schema()` | 新增独立查询模块，逐条推进不调用它。 |
| 输出配置 | `schema`、`output_keys`、`g_index` 等是可赋值属性，缓存及索引依赖它们 | 明确只读职责，将运行时管理属性收口；不承诺整个 Python 对象不可变。 |
| 输出存储 | `_storage_dtypes()` 在构造在线缓存时调用，batch 又读取当时的 schema | 共享一份实例输出存储配置，避免不同阶段重新解释可变配置。 |
| 无 schema 的输出 | 首次结果冻结顶层字段，但只检查是 dict，未显式检查键为 str | 补充首次字段检查，使 `dict[str, Any]` 的输出协议不依赖缓存是否开启。 |
| 结果引用 | object 列可能持有可变对象；用户和算法都能保留引用 | 明确发布后只读，输入跨调用保留需要复制；不默认逐条深复制。 |
| replay | [utils.py](../../sigma2/core/utils.py) 使用 `step(**inputs)`、本次输入范围回填、提前检查输出格式 | 保留，补充位置限定参数、空输入和失败范围的说明。 |
| core 对 pyta2 的依赖 | 使用 Schema、Space 相关存储信息、DequeTable、VectorTable 和输出格式转换 | 当前是通用计算依赖，不是市场 family 依赖；不为“纯 core”重写这些组件。 |

例如，构造时按 float dtype 建立在线缓存，之后替换 `operator.schema`，现有 batch 会按新 schema 建表，而旧缓存仍保留旧配置。这是配置边界薄弱，不代表正常、未修改配置的计算已经出错。修复应围绕固定实例配置，不加入热路径动态迁移。

## 4. core 组织方案比较

| 方案 | 优点 | 代价 | 决定 |
| --- | --- | --- | --- |
| 所有新逻辑继续进入 operator.py | 文件少 | 生命周期与反射、描述、存储规则耦合 | 不采用。 |
| 保留小核心，提取两个明确的辅助模块 | 职责清楚，用户入口基本不变 | 增加两个内部文件 | **采用**。 |
| 拆成生命周期、缓存、schema、调度等独立服务 | 可替换性高 | 需要大量配置和协作对象，暂无具体需求 | 不采用。 |
| 移除 core 的全部 pyta2 依赖 | 核心独立 | 复制已有表、Space 和返回格式能力 | 暂不采用。 |

目标目录：

```text
sigma2/core/
  operator.py       # 生命周期、只读状态/配置、input_schema() 的薄入口
  signal.py         # 当前观测结果
  outcome.py        # 固定延迟的历史锚点结果
  input_schema.py   # 签名读取、声明检查、描述结果组装
  _output.py        # 输出字段和共同存储配置的内部辅助
  utils.py          # 保留 forward_step_apply 的现有路径
  __init__.py       # 现有公共类和 replay 导出
```

依赖方向：数据包 base 指向 core；operator 指向描述/输出辅助；replay 指向 operator 及共同输出规则；辅助模块不反向导入市场包或具体算子。

不把 `forward_step_apply()` 再搬回顶层 `batch.py`，不为目录对称破坏已有入口。`_output.py` 使用少量纯函数和私有数据，不新增公共 OutputSpec、存储插件或 provider 接口。

## 5. 生命周期与扩展契约

### 5.1 唯一推进路径

```text
用户调用数据类型 step()
  -> Python 参数绑定 / 该入口的显式整理
  -> super().step()
  -> rOperator.step()
  -> forward()
  -> 输出字段检查
  -> 在线缓存追加
  -> 返回当前调用结果
```

- 数据类型 `step()` 是用户入口；`forward()` 是扩展钩子，直接调用不会推进索引、检查结果或管理缓存。
- 每个入口只调用一次 `super().step()`；不得在入口和 forward 中分别推进核心状态。
- 实现普通指标只需要实现所选数据基类的 `forward()`，不重复写 step。定义新的输入契约时才写一个薄 step。
- 输入查询读的是实际 step，不自动从 forward 拼出虚构签名。直接继承 `rSignal` 且只实现 forward 的类，查询结果仍是 core 的可变参数；需要可查询的固定入口时显式声明 step。

### 5.2 索引和失败

- 初始 `g_index=-1`，进入核心计算后先增加；第一次 forward 看到 0。
- Signal 的 `result_index=g_index`；Outcome 的 `result_index=g_index-n_forward`。负结果索引表示尚无历史锚点。
- 进入计算前设置失败锁；forward、输出检查、在线缓存全部成功才解除。异常原样传播，不统一吞成 NaN。
- 已进入核心后失败，实例不可继续，后续调用报 RuntimeError 并提示新建重放。索引、子对象和缓存可能已部分变化，不自动回滚。
- 在核心之前被 Python 参数绑定或输入入口拒绝，实例不推进。例如固定签名缺少参数，与直接调用可变参数 core 后在 forward 发生参数错误，不是同一错误边界。
- 构造时的参数错误使用 TypeError / ValueError；输入 schema 定义错误在查询时报错，不锁定实例；具体算法对缺失返回 NaN 属于成功观测。
- 实例不保证线程安全和重入。重复调用不是幂等操作；重试应由上游确认是否需要新建重放。

保留当前单向生命周期，不增加 reset、末根重算、隐式重试或按时间去重。索引表示尝试处理的位置；发生故障后不承诺它仍是最后成功位置。

## 6. 输出配置与缓存

### 6.1 配置与状态的只读边界

建议将 `schema`、`output_keys`、`used_fields`、`g_index` 的公开绑定改为只读属性，保持属性名不变，内部使用私有属性管理。`n_backward/n_forward/buffer_size` 已经只读，继续保持。

- schema 只在构造时指定；动态改变输出协议需要新建实例。
- `used_fields` 构造时规整为 tuple 或 None，仍是元信息，不参与逐条输入检查。
- `output_keys` 有 schema 时在构造时确定，否则从首个合法结果确定；空结果 `{}` 也确定为空字段集合，不能先返回空字典预热，后续再新增字段。
- `g_index` 由 core 推进，外部和具体算法只读取。

只读属性防止重新赋值，不等于递归冻结 pyta2 Schema/Space。传入的 Space、通过 `schema` 或 `meta_info` 取得的描述，以及 `outputs` 表均应只读使用。深层原地修改属于不支持的操作；本轮不包装整个 pyta2 对象图，也不恢复深复制算子状态。

### 6.2 在线与批量共用输出存储配置

有输出 schema 时，在实例创建时确定输出字段顺序、存储 dtype、缺失哨兵；无 schema 时，在首个合法结果到达后确定字段及 object 存储。在线缓存和 replay 从同一份实例配置获得所需信息，不在不同阶段重新读取并解释外部可变的 schema。

内部可以用私有 tuple / dict 保存，不新增用户必须构造的对象：

| 输出 | 存储规则 |
| --- | --- |
| 有 schema，标量且缺失哨兵不为 None | 沿用 Space 的 dtype。 |
| 多维值或缺失哨兵为 None | object，保留数组或 None。 |
| 无 schema | 首次确定字段，全部使用 object，不从首个数值猜 dtype。 |

这些规则已经存在，重构只是确定唯一配置来源。字段映射应是实例自己的副本；可变的缺失哨兵仍按发布后只读约定使用，不能声称浅副本提供深层隔离。

`buffer_size=0` 禁用在线缓存，不改变输出字段检查和 batch 规则；`-1` 无界保留结果，用户承担内存增长。

顶层必须返回 dict，首次确定的键必须是字符串。以后集合必须相同，返回字典的插入顺序可以不同，表按已确定的字段顺序组织。检查的是顶层结构，不自动校验每个值是否满足 Space 的范围或嵌套行情格式。

### 6.3 输入和结果的所有权

- 输入只读借用到本次调用结束。算法跨调用保留历史时，只复制所需内容；基类不深复制每份输入。
- 算法返回结果后，不得在下一次调用中原地改写已经发布的字典、数组等可变值。递推状态若要继续写，应与发布值分离。
- 用户只读使用返回结果和缓存；需要独立修改时自行复制。object 结果可能共享引用，不承诺自动隔离。
- 公共 `outputs` 目前暴露 pyta2 表；本轮保持读取接口，不引入新的只读表代理。不支持外部 append/update 改写它。

## 7. 输入 schema：保留查询，缩小机制

### 7.1 方案比较

| 方案 | 优点 | 代价 | 决定 |
| --- | --- | --- | --- |
| 只靠 Python 注解 | 信息与代码邻近 | 现有签名大量未注解；嵌套字段及数值语义还需额外约定 | 本轮不作为查询的自动来源。 |
| 顶层签名反射＋显式值结构 | 调用形式不会重复维护；描述行为确定 | 扩展作者选择提供结构声明 | **采用**。 |
| 签名＋注解解析＋声明自动合并 | 能利用更多信息 | 联合类型、继承和冲突规则复杂，容易产生貌似精确的错误描述 | 不采用首版。 |
| 输入描述兼做逐条验证和转换 | 可用于接入校验 | 改变计算开销与已确定的输入透传原则 | 不采用。 |

`rOperator.input_schema()` 是 classmethod，内部调用 input_schema 模块。查询不实例化、不创建缓存、不消费输入、不推进状态。初版不缓存查询结果，避免 monkey patch、继承声明和可变返回值带来的失效规则；若有实测需求再优化。

### 7.2 调用契约与值结构各有一个来源

实际 `step()` 的签名决定参数名、顺序、kind、required 和 default。排除实例接收者，保留位置限定、位置或关键字、仅关键字、可变位置、可变关键字五类参数。

- 普通参数没有默认值时 `required=True`。
- `*args/**kwargs` 的 `required=False`，不为其伪造默认值。
- 有默认值时返回原默认对象；没有默认值时省略 default 键。
- `required` 表示必须传入，不表示值不能是 None。

`input_schema_details` 类属性按参数名描述值本身。它不重复声明顶层 kind/required/default；没有声明的参数返回 `{"type": "unknown"}`，不读取或求值注解作为兜底。

普通类属性继承规则就是声明规则：子类未声明时继承；子类声明后**整份替换**，不自动逐参数或递归合并。希望只覆盖一个参数时显式展开：

```python
class rExample(rBundleSignal):
    input_schema_details = {
        **rBundleSignal.input_schema_details,
        "bundle": {
            "type": "mapping",
            "keys": {"type": "string"},
            "values": {"type": "number"},
        },
    }
```

`input_schema_details = {}` 明确清空继承声明。父类和共享嵌套声明视为只读，子类替换节点而不原地修改。多重继承遵循正常 Python 属性查找，不额外实现一套 schema MRO。

声明中的参数必须存在于实际 step 签名；即使存在 `**kwargs`，也不把任意声明键当成隐藏参数。声明名过期时报 ValueError；节点结构或类型词汇不合法时报 TypeError 或 ValueError，并说明类、参数和路径。未声明是 unknown，错误声明不能静默降级为 unknown。

### 7.3 最小描述词汇

schema 是只供查询的 Python 字典协议，不是完整 JSON Schema，不引入 validator 或注册表。

| 节点 | 描述内容 |
| --- | --- |
| `unknown` | 没有提供可靠结构；不是“不允许任何值”。 |
| `number` | 数值语义，不强制 float 转换，也不保证有限。 |
| `boolean` / `string` | 布尔或字符串语义。 |
| `mapping` | `keys` 和 `values` 分别是节点，适合动态 symbol。 |
| `object` | 字段记录的 `fields`；每个字段包含 required 和 schema；显式 `allow_extra`。这里指具名字段映射，不隐含属性访问。 |
| `sequence` | `items` 是一个节点，描述同种元素的有限有序序列。 |
| `tuple` | `items` 是节点列表，描述固定位置和长度，例如盘口的价格/数量二元组。 |

所有节点可声明 `nullable: True/False`；省略表示可空性未知，不以 required 或默认值自动推导。简单标量节点可附加非空的 `enum` 列表；例如成交方向是 `{"type": "string", "enum": ["buy", "sell"], "nullable": True}`。None 由 nullable 表达，不重复放进 enum。

首版不支持任意联合、递归引用、条件必需、Python 类型对象、表达式默认值和自定义节点插件。需要复杂联合时可保留 unknown，并在具体算子契约说明；不能接受一个非法节点然后假装已解析。声明必须是无环的字典/列表结构；查询时检查描述本身，不检查行情数据。

### 7.4 查询结果示例

最高频的单 K 线入口由 `_KlineStep` 提供值结构声明，查询结果中的调用形式仍来自真实签名：

| 参数 | kind | required / default | 值结构 |
| --- | --- | --- | --- |
| open/high/low/close | positional_or_keyword | True；无 default | number |
| volume | positional_or_keyword | False；None | number，nullable=True |
| open_time | keyword_only | False；None | unknown，nullable=True |
| is_missing | keyword_only | False；False | boolean |

表中的类型是输入约定，不恢复已删除的逐条类型校验。K 线具体实例的 `used_fields=("close",)` 也不允许从签名中省略 OHLC 参数。

以下是拟议 `rBundleSignal.input_schema()` 的完整基础形态：

```python
{
    "parameters": {
        "bundle": {
            "kind": "positional_or_keyword",
            "required": True,
            "schema": {
                "type": "mapping",
                "keys": {"type": "string"},
                "values": {"type": "unknown"},
            },
        },
        "time": {
            "kind": "keyword_only",
            "required": False,
            "default": None,
            "schema": {"type": "unknown", "nullable": True},
        },
    },
}
```

K 线截面排名可声明如下 bundle 值结构；其入口仍从实际签名获得 `open_time` 和 `has_missing`，不会被替换成通用 Bundle 的 time：

```python
{
    "type": "mapping",
    "keys": {"type": "string"},
    "values": {
        "type": "object",
        "fields": {
            "close": {
                "required": False,
                "schema": {"type": "number", "nullable": True},
            },
            "is_missing": {
                "required": False,
                "schema": {"type": "boolean"},
            },
        },
        "allow_extra": True,
    },
}
```

盘口算子的 values 可描述 bids/asks 及其二元档位序列；成交窗口的 values 可描述成交记录序列。不统一向所有 value 注入 close、is_missing、event_time 等字段。

返回参数字典和描述容器是独立副本，修改查询结果不改变类声明。唯一例外是签名中的 default 保留原对象身份，调用方必须只读使用；因此整个查询结果不保证能直接 JSON 序列化。当前内置入口使用 None/布尔等简单默认值。

### 7.5 与输出 schema、used_fields 的关系

- `input_schema()`：类级结构说明。
- `schema`：实例级输出 Space 描述，继续复用 pyta2。
- `used_fields`：实例实际读取的字段元信息。

三者不能互相代替。类级结构不能推出固定权重成员、构造参数选择的字段、条件完整性或真实数据可得时间。首版不提供“验证这个输入一定能算”的承诺，也不设计自动生成有效输入的工具。

## 8. 批量重放保持的边界

`forward_step_apply(data, operator, ...)` 从已有实例继续，每条输入是传给 `step(**inputs)` 的映射。它不把不同数据格式自动转换成同一签名。

1. 固定输入的普通参数和关键字参数都可重放。位置限定参数或必须通过 `*args` 提供的数据不能由当前行映射表达；schema 如实报告签名，不意味着 replay 支持所有 Python 调用形式。本轮不增加通用调用封装对象。
2. 输出格式及可选依赖在消费输入前检查，维持现有行为。
3. 每次成功调用追加本次范围的一行。Signal 写当前行；Outcome 按历史锚点回填，本次范围之前的锚点丢弃，尾部未成熟行保留缺失哨兵。
4. 在线 `outputs` 按调用顺序缓存返回结果；它不是批量对齐后的历史表，不能把两者行位置直接混为一谈。
5. 空输入不推进实例：有输出 schema 时保持既定空列；无 schema 时维持当前空字典结果，不因新增输入 schema 猜输出字段。
6. core 内失败锁定算子；输入迭代器失败或 batch 在成功 step 之后整理结果失败，不自动撤销之前的推进，也不保证能够继续原批量调用。调用方需要可恢复的处理时，负责保存可靠输入并新建重放。
7. object 结果可能共享嵌套引用，批量不额外深复制。

## 9. 性能与资源边界

- `input_schema()` 的成本与签名参数数和显式描述节点数有关；无行情依赖，不进入 step 热路径。
- core 每步工作与顶层输出字段数有关，包括字段检查与缓存写入；不能把整个数值算法宣称为 O(1)。
- 固定容量在线缓存最多保留 buffer_size 行，但一行可以包含较大的 symbol 映射或数组；缓存行数不能代替内存字节上限。无界缓存持续增长。
- batch 消费有限 iterable 并累计本次全部输出，内存随本次行数及单行结果大小增长；不声明支持无限流返回。实时计算使用 step。
- 具体 Bundle 算法的复杂度由算法决定，例如现有收益率排名含排序，历史存储随 lag 和各截面成员数增长。基类不持有每个 symbol 的全量历史。
- 不为未经测量的性能问题新增缓存池、行写入器封装或可选验证模式；共享输出配置属于一致性优化。

## 10. 实施拆分和兼容性

这是一份设计，不是已完成的实现或测试报告。后续可独立制定计划：

1. 数据包 base/utils 整理与通用 Bundle：按配套文档执行，保持高频 K 线签名。
2. 输入 schema：增加查询辅助与基类方法，为已有入口提供声明，不改变逐条运行路径。
3. core 输出契约：收口只读属性、共用存储配置、首次字符串字段检查，并补齐引用与 replay 文档。

第 2、3 项各自可实施，不要求先完成通用 Bundle。每项在实施前建立 PLAN，完成后 review、记录 OUTCOME 和 INDEX，再按仓库规则提交推送。

公共类名、构造参数、schema 参数名、forward_step_apply 路径和结果字典形式保留。禁止给 g_index/output_keys 等属性赋值是有意收紧扩展契约，实施时检查仓内及已知调用方；不能声称对修改这些属性的自定义类完全兼容。

已有 tests 中大量检查 reset、update_last 和旧输入对象。验收需要选择仍有效的契约并迁移相应测试，不能用历史测试名称或旧通过数量代替验证。本轮未运行测试或示例，未更改 pyta2 依赖或用户工作区配置。

## 11. 三轮查漏补缺及验收要点

### 第一轮：用户接口

- 单 K 线和多 K 线调用无新增对象、嵌套层或 schema 前置步骤。
- 各数据基类扩展只实现 forward，新输入协议才写 step。
- 查询类而非实例；结构说明与计算充分条件明确分开。
- 继承采用普通属性规则，未提供类型得到 unknown，错误声明得到可定位错误。

### 第二轮：状态和数据正确性

- 参数绑定错误、计算错误、输出错误、在线缓存错误、批量整理错误有各自边界。
- 首次输出固定顶层字段，空结果和动态嵌套 symbol 不混淆。
- 输入复用、子算法递推和结果发布的引用责任明确；不声称只读属性深冻结 Space。
- 在线与批量使用同一输出配置，Outcome 仍区分输出时点和历史锚点。

### 第三轮：范围和演进

- core 不导入任何市场 family；没有新建调度、自动同步或输入验证层。
- 不把辅助提取扩展为公共 provider 框架，不重写 pyta2。
- 文档描述新增功能均标记为待实施，历史测试不作为已验证证据。
- 实施验收至少覆盖：类级查询和声明继承；默认值身份与结构副本；无效声明不推进实例；输入复用；错误锁定；缓存关闭与开启的字段一致性；标量/None/数组输出；Outcome 对齐；空 batch；现有实例续放；只读配置与共享存储规则。
