# 通用多 symbol Bundle 与输入 schema 设计

- 创建时间：2026-11-11 22:08 CST
- 状态：设计草案，供评审；尚未实施。
- 范围：通用 Bundle 的输入和生命周期、输入 schema、现有 K 线截面算子的迁移。

## 1. 背景和目标

当前 `sigma2.kline_bundle` 的共同入口实际只把 symbol 到数据的映射交给 core，但名称、`open_time` 和基类限定在 K 线。盘口快照、多 symbol 成交以及跨品种信号也需要类似的截面入口。用户希望简化这一层，用 `bundle` 支持多种数据，并能通过类查询输入字段及其类型。

本设计采用用户选择的方向：**每次 `step()` 输入一个多 symbol 截面**。Bundle 只负责组织多个 symbol 的数据；各 symbol 的具体内容由使用它的算子说明。数据来源负责截面构造、时间对齐、完整性和去重，Bundle 不自动推断或转换数据。

这里的 Bundle 是一种**输入组织方式**，不是只能容纳 K 线的新行情记录类型。一个算子仍应明确它需要的是 K 线、盘口、成交序列还是组合记录，以便调用方知道怎样构造输入。

## 2. 代表性使用场景

| 场景 | 输入 | 期望 |
| --- | --- | --- |
| K 线截面收益率排名 | 多个 symbol 的 K 线字段 | 每次推进一个共同截面，沿用 `lag` 步和现有缺失规则。 |
| 固定权重价格指数 | K 线字段与构造时给定的权重 | 保留当前对成分和 `has_missing` 的约定。 |
| 实时市值加权指数 | 每个 symbol 的价格和 `market_cap` | 保留当前市值、缺失和精度语义。 |
| 盘口价差比较 | 每个 symbol 的 `bids`、`asks` | 一次返回各 symbol 的价差或截面统计。 |
| 最近成交价截面 | 每个 symbol 的一条最近成交 | 用于价格比较；不把重复出现的成交自动当作新成交。 |
| 时段成交量比较 | 每个 symbol 在一个时段内的成交序列 | 每个序列由上游按约定分窗并排序；空序列与未知数据区分。 |
| 联合盘口与成交 | 每个 symbol 对应一个包含两类数据的组合记录 | 由具体算子声明结构；上游负责同一截面的时间口径。 |
| 查询输入 | 通过算子类查询字段、类型、参数种类和嵌套结构 | 不需要实例化，也不触发逐条校验。 |
| 自定义截面 Outcome | 一次输入一个截面，等待后续截面 | 结果属于固定步数之前的锚点截面。 |

## 3. 方案比较

| 方案 | 优点 | 问题与决定 |
| --- | --- | --- |
| 为 K 线、盘口、成交分别建立 Bundle 基类 | 每种输入的名称和字段直观 | 多份基类重复表达同一种多 symbol 截面；新增数据种类继续复制，暂不采用。 |
| 一个通用 Bundle，根据字典字段自动判断数据类型 | 使用时不用声明类型 | 字段可能重叠，混合记录和空截面无法可靠识别；隐式推断不采用。 |
| 一个通用 Bundle 基类，具体算子声明每个 symbol 的数据结构 | 入口浅，支持复用和不同数据；允许列表及组合记录 | 需要描述具体内容；**采用**。 |
| 把逐笔事件流、跨 symbol 对齐和截面都纳入 Bundle | 接入事件源看似方便 | 引入缓存、分窗、迟到事件和同步状态；超出信号库的共同输入职责，不采用。 |

## 4. Bundle 的输入模型

```python
bundle = {
    "BTC": payload_for_btc,
    "ETH": payload_for_eth,
}
```

- 容器使用普通 `Mapping[str, Any]`，键是上游提供的 symbol；不要求构造专门的 Bundle 对象。
- 单次输入中每个 value 的结构由具体算子约定。value 可以是 K 线字典、盘口字典、一条成交、成交序列，或明确声明的组合记录；基类不按字段猜测数据类型。
- 同一个算子应对各 symbol 使用它声明的同一种 value 结构。组合记录可同时包含 `kline`、`orderbook`、`trades`，但对应数据的拼接与对齐仍由上游完成。
- 未出现的 symbol 可能是未选入本次截面，也可能是缺失；通用 Bundle 不推断原因。具体算子若有固定成分或其他约束，应单独说明。
- 知道某 symbol 在一个成交窗口内**没有成交**时可以传 `[]`；没有收到该 symbol 的数据不能静默转换为 `[]`，其语义由数据源和具体算子约定。
- `is_missing` 等 value 内部字段没有全局魔法。现有 K 线收益率排名按自己的规则检查 Bar 的 `is_missing`；通用 Bundle 不替所有算子检查或改写它。
- 跨交易所、重名代码的标识应由上游统一，例如使用带市场前缀的 symbol。Bundle 不内建符号解析或资产目录。

下面只是输入形状示例，不代表新增了这些算子：

```python
# 每个 symbol 是一份盘口快照。
books = {
    "BTC": {"bids": [(99.0, 2.0)], "asks": [(101.0, 1.0)]},
    "ETH": {"bids": [(49.0, 1.0)], "asks": [(50.0, 3.0)]},
}

# 每个 symbol 是一个窗口中的成交序列；ETH 已知无成交。
trades = {
    "BTC": [
        {"price": 100.0, "volume": 2.0, "side": "buy"},
        {"price": 101.0, "volume": 1.0, "side": "sell"},
    ],
    "ETH": [],
}
```

盘口档位顺序不由 Bundle 改写。成交是事件，不是天然连续的状态：最新成交截面可以在多个时点重复出现同一成交；窗口序列则应明确窗口边界、事件顺序和是否允许重叠。把重复成交重复累计、把无成交误认为缺失，都会改变因子含义，应由具体算子和上游协议避免。

## 5. 基类接口与生命周期

建议使用与数据类型无关的入口：

```python
from collections.abc import Mapping
from typing import Any

class _BundleStep:
    family = "bundle"

    def step(
        self,
        bundle: Mapping[str, Any],
        *,
        time: Any = None,
        has_missing: bool = False,
    ) -> dict[str, Any]:
        return super().step(bundle, time=time, has_missing=has_missing)

class rBundleSignal(_BundleStep, rSignal):
    pass

class rBundleOutcome(_BundleStep, rOutcome):
    pass
```

代码表达目标结构，尚未实现。`rBundleSignal` 和未来需要时的 `rBundleOutcome` 共享同一个输入层，分别继承 core 的 Signal 和 Outcome 生命周期；具体算子只需实现相同参数的 `forward()`。它们和现有 K 线因子均通过 `rOperator.step()` 推进，`forward_step_apply()` 也逐条调用该入口。当前没有 Bundle Outcome 因子，不必仅为对称性提前建立空实现。

| 参数 | 含义 |
| --- | --- |
| `bundle` | 必需；symbol 到算子所需记录或记录序列的映射，可按位置或关键字传入。 |
| `time` | 可选且只能按关键字传入；本截面的时间标签，由调用方约定具体口径。 |
| `has_missing` | 可选且只能按关键字传入；上游报告截面存在缺失或无效输入时为真。 |

`time` 使用中性名称以支持多种数据。保留 `open_time` 作为所有 Bundle 的共同参数会把 K 线术语带入盘口和成交；同时维护 `time` / `open_time` 两套别名会增加冲突规则。本设计推荐统一 `time`，并在迁移中明确现有调用需要更名。

例如，现有收益率排名迁移后的调用可以保持简短：

```python
# 以下是目标接口示意；当前代码仍使用 open_time。
rank = rKlineBundleReturnRank(lag=1)
rank.step({"BTC": {"close": 100}, "ETH": {"close": 200}}, time=0)
rank.step({"BTC": {"close": 110}, "ETH": {"close": 190}}, time=1)
# 第二次结果：{"rank": {"BTC": 2, "ETH": 1}}
```

### 时间和可得性

1. 每次 `step()` 推进一个截面；`g_index` 和 `lag` 表示逻辑步数，不是实际时长。相同 `time` 的两次调用仍是两次观测。
2. `time` 只是标签，不自动排序、去重、补齐时点、判断数据是否过期或推断真实可得时间。需要规律时间轴的因子由上游按约定提供截面，包括必要的空截面。
3. 上游确定截面点或窗口边界，以及每个 symbol 的事件时间、接收时间和可使用时间。对研究或回测而言，只能使用决策时已经可得的数据；以 K 线开盘时间标记的最终收盘价不意味着开盘时已经可用。
4. 对最新盘口或最新成交，上游应明确允许的陈旧程度；对成交窗口，应明确窗口是否重叠。Bundle 不前向填充，也不负责把窗口变成逐笔事件流。

### 缺失和输出

- `has_missing=False` 不是自动证明所有市场 symbol 都已到齐；具体算子可以要求调用方保证所需范围完整。`True` 只能表示上游报告有缺失，不能推断缺少哪个 symbol 或字段。
- 通用基类不校验类型、不自动填充、不修改 value；各算子自行规定空截面、缺失字段和无效值如何计算。现有固定权重和市值加权类继续维持各自的分支行为。
- Signal 结果属于当前截面；Outcome 的 `result_index = g_index - n_forward`，结果属于历史锚点截面。成员变化时如何对齐锚点成员由具体 Outcome 定义，不能默认套用当前成员。
- 结果仍是以输出字段为键的字典。例如横截面结果可为 `{"spread": {"BTC": 2.0, "ETH": 1.0}}`，聚合结果可为 `{"index": 150.0}`。结果、schema 和缓存规则继续由 core 管理；嵌套可变结果可能与缓存共享引用，应视为只读。
- 批量使用 `forward_step_apply()`，每条输入为 `{"bundle": ..., "time": ..., "has_missing": ...}`，只返回本次输入范围并沿用 Outcome 对齐；不引入第二套 Bundle 批处理框架。时间标签不会自动成为结果索引。
- 基类不为每个 symbol 自动保存子算子或整份历史，额外状态由具体算子决定。已有输出缓存仍可能持有结果引用；计算失败后实例按 core 规则锁定，需要新建实例并重放。实例不保证并发或重入安全。

## 6. 输入 schema

### 为什么独立于输出 schema

当前 `rOperator.schema` 是输出 schema，使用 pyta2 的 `Schema` / `Space`；它的字段值必须是 `Space`，不直接描述 `step()` 的参数种类或 symbol 到嵌套记录的映射。本设计使用独立的 **`input_schema()`** 描述输入，保留现有输出 `schema` 的含义。

### 类级接口

```python
rKlineSignal.input_schema()
rBundleSignal.input_schema()
rKlineBundleReturnRank.input_schema()
```

- `rOperator` 提供 `@classmethod input_schema()`；不创建实例，不推进算子，不要求数据输入。
- 返回普通字典，schema 字典及嵌套结构是独立副本，调用方修改它们不会改写类声明。签名中的任意 `default` 保留原对象以保持其身份，不承诺复制，调用方应视为只读。schema 是元信息，不自动校验或转换每条输入。
- 顶层 `parameters` 按 `step()` 定义顺序列出参数，排除实例接收者；每项描述 `kind`、`required`、可选 `default` 和值的 `schema`。
- `kind` 保留 Python 的位置限定、位置或关键字、仅关键字以及可变参数区别。`required` 表示调用时是否必须提供，和一个字段是否允许 `None` 分别表示。
- 参数名、调用方式与默认值从实际 `step()` 签名取得，不再手写另一套参数列表。对于 `*args` 和 `**kwargs`，如实返回对应可变参数种类，不将它们当作必需字段。
- 具体值的类型、可空性及嵌套结构由数据类型或具体算子声明。显式声明优先；没有声明时可采用能可靠解析的类型注解，未标注、注解为 `Any` 或无法解析时为 `unknown`，不猜测。类型注解在源码中可能因延迟求值而是字符串；无法解析时仍返回 `unknown`，不把字符串误认作实际 Python 类型。
- 建议使用 `input_schema_details` 类属性按参数名声明值结构；它只补充值本身的信息，不重复声明顶层参数的 `kind`、`required` 或 `default`。派生类可为 `bundle` 声明更具体的 value schema。声明中不存在于实际签名的参数，应在查询 schema 时报告定义错误，而不是悄悄发布不一致信息；`step()` 不做这一检查。
- `rOperator.step(*args, **kwargs)` 本身没有固定市场字段；查询该基类时应如实报告可变参数，不能伪造 K 线字段。覆盖 `step()` 的自定义类应同步其值结构声明。
- 简单自定义算子仍可只实现 `forward()`；不声明额外结构不影响计算，对应 schema 如实保留基类已知信息和 `unknown`，不强迫每个算子编写 schema。

建议 schema 的最小类型词汇覆盖 `unknown`、`number`、`boolean`、`string`、`mapping`、`object`、`sequence` 和固定项 `tuple`；`number` 表示数值语义，不强制数据转换或逐条类型检查，也不代表数值一定有限，NaN 的含义由算法约定。对象字段记录自身 schema 及是否必需；映射有 key/value schema；序列有 item schema。`nullable` 与缺省是不同概念，未声明 `nullable` 时其可空性未知。有可靠解析且与显式声明相容的 Python 类型注解时，以 `python_type` 附加对应类型或 typing 对象，供程序查询；它同样不代表运行时检查。例如 `has_missing: bool` 可提供 `python_type: bool`。返回值是 Python 字典，不保证可直接 JSON 序列化，不急于引入额外的 schema 框架。

### 单 K 线 schema 示意

下面是 `rKlineSignal.input_schema()` 的目标形态，字段值类型由 `_KlineStep` 声明，参数调用方式和默认值由其 `step()` 签名取得；现有代码尚未提供该方法：

```python
{
    "parameters": {
        "open":  {"kind": "positional_or_keyword", "required": True, "schema": {"type": "number"}},
        "high":  {"kind": "positional_or_keyword", "required": True, "schema": {"type": "number"}},
        "low":   {"kind": "positional_or_keyword", "required": True, "schema": {"type": "number"}},
        "close": {"kind": "positional_or_keyword", "required": True, "schema": {"type": "number"}},
        "volume": {
            "kind": "positional_or_keyword", "required": False, "default": None,
            "schema": {"type": "number", "nullable": True},
        },
        "open_time": {
            "kind": "keyword_only", "required": False, "default": None,
            "schema": {"type": "unknown", "nullable": True},
        },
        "is_missing": {
            "kind": "keyword_only", "required": False, "default": False,
            "schema": {"type": "boolean", "python_type": bool},
        },
    },
}
```

`is_missing` 的 `python_type: bool` 示例要求在目标实现中提供可解析的类型注解或明确类型声明；当前 `_KlineStep` 尚未标注它。字段类型只描述约定，仍由上游提供数据，不恢复此前删除的类型检查或 NaN 自动替换。

### Bundle schema 示意

以下表示 **K 线类截面的输入结构**，省略部分已知字段的具体类型描述；不是已实现的 API：

```python
{
    "parameters": {
        "bundle": {
            "kind": "positional_or_keyword",
            "required": True,
            "schema": {
                "type": "mapping",
                "keys": {"type": "string"},
                "values": {
                    "type": "object",
                    "fields": {
                        "close": {
                            "required": False,
                            "schema": {"type": "number", "nullable": True},
                        },
                        "market_cap": {
                            "required": False,
                            "schema": {"type": "number"},
                        },
                        "is_missing": {
                            "required": False,
                            "schema": {"type": "boolean"},
                        },
                        # open、high、low、volume 等按同一方式描述。
                    },
                    "allow_extra": True,
                },
            },
        },
        "time": {
            "kind": "keyword_only", "required": False, "default": None,
            "schema": {"type": "unknown", "nullable": True},
        },
        "has_missing": {
            "kind": "keyword_only", "required": False, "default": False,
            "schema": {"type": "boolean"},
        },
    },
}
```

`rBundleSignal` 的通用 value 类型是 `unknown`；需要盘口的算子可声明 value 是含 `bids`、`asks` 的对象，每档是价格和数量组成的二元组。成交窗口算子可声明 value 是成交对象的序列。需要混合数据时，value 是显式声明了多个子字段的对象，不依赖自动识别。

例如，Bundle 基类的 `input_schema_details` 可只描述 `bundle` 是字符串键映射且 value 为 `unknown`；K 线截面算子通过同名声明提供更具体的 K 线 value 结构。`time` 和 `has_missing` 的调用方式与默认值仍从实际签名获得；必要的额外类型信息由注解或显式声明补充。各类声明应视为只读，子类需要更改时创建自己的声明，不原地修改父类字典。

例如，程序可以查询 `rKlineBundleReturnRank.input_schema()["parameters"]["bundle"]["schema"]["values"]["fields"]["close"]`，得到上面 `close` 的类型及是否必需。单 K 线的 `open`、`high`、`low`、`close`、`volume` 也应在 `_KlineStep` 中声明值类型；它们的参数种类、必需性和 `volume=None` 默认值来自实际签名。

K 线字段的**类型描述**可以复用，但必需性不能简单复制：单 K 线 `step()` 的 OHLC 是必需参数，现有 Bundle 收益率排名允许某个 Bar 缺少 `close` 并输出缺失；市值加权在 `has_missing=False` 时需要所用价格和 `market_cap`。上述 Bundle 示例的可选字段表示共同结构，不承诺任意具体算子都能在所有字段缺失时正常计算。

类级 schema 描述输入结构；`used_fields` 继续描述具体实例实际使用的字段，例如某个价格指数构造时选择 `field="close"`。`used_fields` 不是完整校验规则：固定成分、`has_missing` 和成员范围也会影响实际需求；若以后需要实例级输入需求，再单独设计，不预先把它塞进类级 schema。

## 7. 目录、命名与迁移

建议目录：

```text
sigma2/
  core/                      # 通用生命周期和 input_schema() 机制
  kline/                     # 单 symbol K 线
  orderbook/                 # 单 symbol 盘口
  trade/                     # 单 symbol 逐笔成交
  bundle/
    base/
      _input.py              # 共同截面输入
      signal.py              # rBundleSignal
      outcome.py             # 有 Bundle Outcome 需求时再增加
    utils.py                 # 需要共享时的 Bundle schema 辅助
    kline/
      return_rank.py
      weighted_index.py
```

K 线截面因子仍是 K 线语义，保留 `rKlineBundleReturnRank`、`rKlineBundleFixedWeightIndex`、`rKlineBundleMarketCapWeightedIndex` 及其批量函数名；它们放到 `sigma2.bundle.kline`，由 `sigma2.bundle` 和根级 `sigma2` 导出。盘口或成交截面有实际算子时再增加相应目录，不先建立空实现或镜像整个单 symbol 指标库。

| 当前入口或行为 | 建议目标 | 影响 |
| --- | --- | --- |
| `rKlineBundleSignal` | `rBundleSignal` | 自定义子类需要改基类名和导入。 |
| `sigma2.kline_bundle` | `sigma2.bundle` / `sigma2.bundle.kline` | 直接导入旧包路径的代码需迁移。 |
| `sigma2.rKlineBundleReturnRank` 等具体因子 | 保留根级具体因子名 | 常用类名不必更改。 |
| `open_time=...` | `time=...` | 逐条调用及批量字典中的字段名均需修改。 |
| `meta_info["family"] == "kline_bundle"` | `"bundle"` | 按 family 分支的调用方需调整。 |
| 类或实例按旧模块路径序列化 | 实际 `__module__` 迁至新包 | 旧序列化数据可能需要迁移。 |

结合此前直接迁移旧路径的偏好，建议不长期保留旧包转发；这属于本次设计建议，不代表旧包已经移除。是否需要短期兼容、何时切换应在实施前结合实际调用方决定。无论迁移方式如何，不改动现有因子的公式、输出字段、排序、窗口长度、缺失和数值精度行为。

## 8. 实施边界与验证要点

设计落地可分为：先完成 core 的输入 schema 查询和各数据类型声明，再建立通用 Bundle Signal 基类，最后迁移现有 K 线截面因子及其调用方；有明确需求时再增加 Bundle Outcome。单 symbol 因子不因为引入 Bundle 而改造成统一包装器。

需要覆盖的要点：

1. 类级 schema：不实例化即可查询；位置或关键字、仅关键字、必需、默认值、可空和嵌套动态键分别正确；未声明字段不被猜测。
2. 基类：Bundle 输入按原值进入 core；时间标签、缺失标志和空映射不触发自动改写。将来增加 Outcome 时复用同一输入层。
3. 旧 K 线因子：排名结果、相等值排序、`lag`、动态成员、空截面、固定成分缺失和极小权重数值与当前约定一致。
4. 盘口和成交：盘口空档与缺 symbol 区分；成交空序列、缺失、重复最新成交及窗口序列分别有明确行为；不假设逐 symbol 事件同步。
5. 批量和 Outcome：继续按一个截面一行推进，保留嵌套输出、空输入、已有实例续放及历史锚点对齐；输入字典使用新的 `time` 字段。
6. 迁移：根级具体因子导出、直接模块路径、`family`、时间参数和序列化变化均有清晰说明；不得将旧路径移除伪装成完全兼容。

## 9. 三轮查漏补缺

1. **概念与接口**：Bundle 只表示截面组织；K 线、盘口和成交 payload 不被合并成同一个固定记录。参数调用方式从真实签名得到，嵌套结构另行声明，类级结构与实例 `used_fields` 分开。
2. **时间与缺失**：`time` 不等于事件发生或数据可得时间；不自动补齐、去重或前向填充。空成交序列、空截面、未选入成员和缺失成员不能混为一谈。
3. **现有行为与复杂度**：现有 K 线因子保留算法和输出，显式列出 `family`、模块路径和 `open_time` 的破坏性迁移；不引入 Bundle 实例、自动类型识别、事件同步器或强制逐条校验。
