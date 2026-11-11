# 多 symbol Bundle 与按数据类型组织的输入设计

- 创建时间：2026-11-11 22:08 CST
- 修订日期：2026-11-12
- 状态：已实施，详见 `docs/dev/PLAN-053-family-base-layout-OUTCOME.md` 至 `PLAN-056-core-output-contract-OUTCOME.md`。文中“拟议”及“尚未实施”保留设计提出时的语境。
- 范围：Bundle 输入模型、各数据包的职责、高频 K 线入口、时间粒度、缺失和迁移边界。
- 配套设计：[core 与输入 schema](core-input-schema-20261112-overview.md)。本文件替代原稿中的通用入口、schema 实现和目录迁移建议。

## 1. 目标与本轮澄清

工作区 `GOAL.md` 指定：sigma2 是按数据分类的量化交易信号库；core 是共同核心，每种 `step(self, ...)` 输入契约对应自己的数据目录，各数据包提供 `base/` 和 `utils.py`。其列举的现有类型包括 kline、trade、orderbook、kline-bundle。

本轮进一步明确：

1. Bundle 表达多 symbol，不规定每个 symbol 对应 value 的字段。
2. “支持 kline、trade、orderbook 等”指支持多种输入格式，不要求一次输入同时包含这些数据。
3. 各类数据的粒度不同；Bundle 不把 K 线、盘口、逐笔成交强制同步为同一种观测。
4. K 线使用频率最高，不能为了通用性要求额外的 `kline` 包装层、模式参数或输入对象。

因此，Bundle 的共同结构只有 `Mapping[str, T]`。具体算子规定 `T` 的结构和一次调用的业务含义。相同的外层结构不代表相同的字段、时间粒度或缺失规则。

本轮不设计包含多种数据源的组合记录，也不建设跨数据源对齐器。以后确有联合计算需求时，另行确定输入与可得性契约；本轮的容器并不禁止自定义复杂 value，但不据此提前增加公共接口。

## 2. 用户与代表性场景

频次为本轮需求的设计排序，不是运行统计。

| 场景 | 频次 | 用户希望提供什么 | 设计要求 |
| --- | --- | --- | --- |
| 单 symbol K 线指标 | 最高 | 原有 OHLCV 参数 | 保持现有 `rKlineX.step()`。 |
| 多 symbol K 线排名 | 高 | `{symbol: bar}` | 直接传 Bar 字段，不再包 `kline`。 |
| 固定权重和市值加权 | 高 | `{symbol: bar}` 及现有配置 | 保持公式、成员和缺失行为。 |
| 自定义 K 线截面 | 中 | 同一种 Bar 结构 | 继承 K 线截面基类，只实现 `forward()`。 |
| 多 symbol 盘口采样 | 中 | `{symbol: book}` | 盘口字段由算子声明，不要求 OHLCV。 |
| 多 symbol 成交窗口 | 中 | `{symbol: trades}` | 每个 value 是已分窗的序列；空序列有明确含义。 |
| 数值截面 | 中 | `{symbol: number}` | 不为一个数字构造行情记录。 |
| 查询输入格式 | 中 | 算子类 | 不实例化即可查参数、字段和类型。 |
| 自定义未来截面结果 | 低 | 按固定粒度推进的截面序列 | 明确历史锚点和成员归属，有需求再实现基类。 |

调用接口面向使用者，优先表达业务输入；core、输入描述和缓存接口面向扩展作者，优先明确状态、类型和所有权。

## 3. 输入模型方案比较

| 方案 | 优点 | 代价 | 决定 |
| --- | --- | --- | --- |
| 所有 value 固定为 OHLCV | K 线容易理解 | 无法自然表达盘口、成交序列和数值 | 不采用。 |
| 所有 value 都是 `{kline, trade, orderbook}` | 可表达联合来源 | 高频 K 线多一层；不同粒度需要额外同步；不符合本轮意图 | 不采用。 |
| 外层固定 symbol 映射，value 由具体算子声明 | K 线保持扁平，其他格式自然可达 | 每个算子必须交代输入和粒度 | **采用**。 |
| 传入任意结构，由基类按字段自动判断格式 | 表面上不用声明 | 空输入、字段重名和不完整记录无法可靠判断 | 不采用。 |
| 自动接收逐笔流、缓存并生成各类截面 | 接入层似乎更方便 | 引入同步、分窗、乱序和迟到数据状态 | 不属于信号库本轮职责。 |

通用性来自不同算子可以使用不同的 `T`，不来自一个算子在运行中任意切换 value 格式。一个算子的输入结构应稳定；可选字段、可空值由该算子声明。

## 4. 调用方式：先保证 K 线简单

### 4.1 现有高频入口保持不变

```python
from sigma2 import rKlineMA, rKlineBundleReturnRank

ma = rKlineMA(5)
ma.step(100, 103, 99, 102, 10, open_time=0)

rank = rKlineBundleReturnRank(lag=1)
rank.step({"BTC": {"close": 100}, "ETH": {"close": 200}}, open_time=0)
result = rank.step(
    {"BTC": {"close": 110}, "ETH": {"close": 190}},
    open_time=1,
)
# result == {"rank": {"BTC": 2, "ETH": 1}}
```

不要求构造 `Bundle` 实例、传 `data_type="kline"`、写 `{"kline": bar}`，也不要求先查询 schema。已有类名、批量函数名、根级导出和 K 线时间参数继续使用。

### 4.2 不同格式的 Bundle

以下只是输入结构，不代表增加了对应内置算子：

```python
# K 线：value 是一份 Bar。
klines = {"BTC": {"close": 100}, "ETH": {"close": 200}}

# 盘口：value 是一份盘口快照。
books = {
    "BTC": {"bids": [(99, 2)], "asks": [(101, 1)]},
    "ETH": {"bids": [(49, 1)], "asks": [(50, 3)]},
}

# 成交窗口：value 是一个窗口内已排序的成交序列。
trades = {
    "BTC": [{"price": 100, "volume": 2, "side": "buy"}],
    "ETH": [],
}

# 数值截面：value 也可以直接是数字。
values = {"BTC": 0.03, "ETH": -0.01}
```

每种结构交给接受该结构的算子。基类不将它们互相转换；也不以首个 symbol 的 value 推断其余 value 类型。

### 4.3 通用基类与专用入口

入口方案比较：

| 方案 | 影响 | 决定 |
| --- | --- | --- |
| 全部算子迁到一个含所有可选参数的签名 | K 线缺失标记泄漏给其他数据；新增格式不断增加参数 | 不采用。 |
| 全部强制改成 `step(bundle, *, time=None)` | 通用入口很小，但当前 K 线完整性信息无处表达 | 不直接替换现有 K 线入口。 |
| 保留高频专用入口，新增最小通用入口 | 少量签名转发重复，用户不用迁移高频调用 | **采用**。 |

目标通用入口为：

```python
from collections.abc import Mapping
from typing import Any

from sigma2.core import rSignal


class _BundleStep:
    family = "bundle"

    def step(
        self, bundle: Mapping[str, Any], *, time: Any = None
    ) -> dict[str, Any]:
        return super().step(bundle, time=time)

class rBundleSignal(_BundleStep, rSignal):
    pass
```

这是拟议接口，尚未实现。运行时 value 使用 `Any` 不表示所有算子都接受任何内容；具体类的输入 schema 和文档描述其 `T`。不为每种 `T` 建立动态注册表或工厂。

现有 K 线截面入口继续是：

```python
step(bundle, *, open_time=None, has_missing=False)
```

`rKlineBundleSignal` 和 `rBundleSignal` 都复用 `rSignal`、`rOperator`，分别通过自己的输入层转交参数。K 线入口不必继承通用 Bundle 基类：二者参数不同，强行建立该继承关系会引入参数翻译和缺失信息传递。十余行转发的重复小于隐藏协议的成本。

自定义算子通常只实现所选基类对应的 `forward()`。需要不同时间或输入参数的另一种稳定协议时，在自己的数据包中定义入口，不向所有算子增加 `**metadata`。

现阶段只增加有明确扩展用途的通用 Signal 入口；`rBundleOutcome` 在出现具体 Outcome 需求时再增加，并复用同一个 `_BundleStep`。

## 5. 时间粒度：共同推进规则，各自业务单位

| 输入类别 | 一次 `step()` 的含义 | 上游应说明 |
| --- | --- | --- |
| K 线截面 | 同一周期的一轮 Bar | 周期、缺席成员、已确认数据和时间轴。 |
| 盘口截面 | 某次决策或采样时可用的盘口集合 | 采样规则、允许陈旧程度、各记录的可得性。 |
| 最近成交截面 | 各 symbol 当时已知的最近一笔成交 | 同一成交可能重复出现，不等同于新增成交事件。 |
| 成交窗口截面 | 各 symbol 在某个窗口内的成交序列 | 窗口边界、开闭区间、排序和是否重叠。 |
| 数值截面 | 一次采样中的数值集合 | 数值的来源和时间口径。 |

所有算子共享的规则仅为：一次成功 `step()` 推进一个逻辑位置。`lag=5` 表示该算子输入序列的五步，不统一解释成五根 K 线、五秒或五笔成交。

- `time` / `open_time` 是所属入口的时间标签，core 不根据它们排序、去重、补时点或检查可得性。相同标签调用两次仍推进两步。
- 需要规则时间轴的算子由上游按规则提交，包括必要的空截面；不提交和提交空截面不同。
- K 线按一分钟推进，盘口按另一采样频率推进，成交按自己的窗口推进；它们不需要共用一条时间轴。
- 一个截面内部是否要求事件时间完全相等，由具体算子决定。盘口采样通常表达同一决策时点的可用状态，不意味着每个盘口的最近更新时间相同。
- 最新成交重复出现在多个截面时，不能自动当成多笔成交累计。计数类算子优先接收不重叠的窗口；特殊去重由具体算法或上游承担。
- 最终收盘价的开盘时间标签不代表该价格在开盘时已可得；研究和回测由上游保证使用当时可得的数据。

## 6. 成员与缺失

通用基类不定义保留字段，不校验行情、不改写值，不推断完整成员集合。每个具体算子必须说明计算范围、缺失表达和输出影响。

| 情况 | 通用层可以知道什么 | 具体算子需要规定什么 |
| --- | --- | --- |
| symbol 未出现 | 该键不在本次输入 | 未选入还是所需成员缺失；不能无依据推断。 |
| 空映射 `{}` | 本次没有提供成员，仍推进一步 | 输出空映射、NaN 或输入错误。 |
| value 为 `None` | 调用方提供了一个空值 | 是否接受整份记录未知；基类不会自动替换为字典。 |
| 某字段为 None/NaN 或字段缺省 | 具体 payload 的信息 | 是否视为缺失、忽略还是错误。 |
| 成交序列 `[]` | 若契约如此约定，已知窗口内无成交 | 不能把未收到数据静默变成空序列。 |
| value 带 `is_missing` | 普通字段 | 只有声明消费它的算子才解释它。 |

`has_missing` 不进入新的通用 Bundle 签名。它在现有 K 线入口中的含义保留：

| 现有算子 | 成员范围 | 现有行为，迁移不得改变 |
| --- | --- | --- |
| 收益率排名 | 当前输入成员，参考共同时间轴上的历史截面 | 忽略全局 `has_missing`；按各 Bar 的标记、close 和参考端点判断；无效成员排名为 NaN。 |
| 固定权重指数 | 构造时正权重成员 | 标记为真时检查所需成员并在缺失时返回 NaN；为假时信任调用方保证输入有效。 |
| 市值加权指数 | 调用方提供且声明完整的当期集合 | 标记为真时返回 NaN；为假时直接计算；空集合或全零市值返回 NaN。 |

这些是已有算法契约，不是推荐所有新算子采用的通用缺失模式。未来要改变 K 线缺失 API，应单独评估调用方和性能，不随目录整理改变。

## 7. 所有权、输出和状态

1. 输入在本次同步调用期间只读借用。调用方在调用期间不得并发修改，算子不得原地修改。基类不做深复制。
2. 调用结束后，调用方可以复用原输入。算子若跨调用保存历史，负责提取数值或保存必要的独立快照，不能仅保存随后会被外部改写的嵌套引用。当前排名保存自己的 close 字典，符合这一规则。
3. `forward()` 返回字段字典。顶层字段在输出 schema 或首次结果中确定，后续固定；嵌套的 symbol 集合可以随截面变化。
4. 输出沿用 `{"rank": {symbol: rank}}`、`{"index": value}` 等形式。嵌套对象可能与在线缓存和批量结果共享引用，调用方应只读使用；需要修改时自行复制。算子发布结果后也不得在后续调用中原地改写已发布的可变内容。
5. Signal 属于当前截面。将来 Outcome 按 `result_index = g_index - n_forward` 归属历史锚点，其成员应由该具体算法按锚点定义，不能直接借用当前成员。
6. 不自动为每个 symbol 创建子算子、保存全量历史或前向填充。额外状态由算法持有，历史窗口按共同截面而非各成员出现次数推进。
7. 实例不支持并发或重入；计算、输出检查和在线缓存失败后按 core 规则锁定，新建实例并重放。

批量仍使用 `forward_step_apply()`：K 线输入行保留 `bundle/open_time/has_missing`，通用 Bundle 输入行使用 `bundle/time`。每行调用对应实例的实际 `step()`，不引入第二套 Bundle replay。时间标签不自动成为结果索引。

## 8. 输入 schema 与实际需求

保留无须实例化的查询入口：

```python
rKlineSignal.input_schema()
rKlineBundleReturnRank.input_schema()
rBundleSignal.input_schema()
```

以上方法尚待实施。通用 Bundle 的 `bundle` 描述为字符串键映射、value 为 `unknown`；具体算子可将 value 声明为 Bar、盘口、成交序列或 number。查询不会扫描输入或推断类型。

schema 只回答调用参数和结构类型，不能单独证明输入足以计算：

- 单 K 线 OHLC 是签名必需参数；排名 Bar 的 `close` 可以缺省并得到缺失结果。这两种必需性不能直接复制。
- 固定权重实例选择 `field="open"` 后需要该字段，不能用类级通用 Bar 描述推导该实例的全部需求。
- `used_fields` 继续描述实例读取字段；固定成员、条件缺失规则、采样粒度仍属于具体算子契约。

查询机制、声明格式、继承和错误规则统一见 [core 与输入 schema 设计](core-input-schema-20261112-overview.md)。本轮不增加自动输入校验、实例级需求推理或 schema 注册服务。

## 9. 目录、命名和兼容性

采用与 `GOAL.md` 一致的按输入契约分包。保留高频 `kline_bundle`，不迁入 `bundle/kline`；新增 `bundle` 是不绑定固定行情字段的多 symbol 入口。

```text
sigma2/
  core/                       # 通用生命周期、描述机制、输出存储和 replay
  kline/
    base/                     # 已有单 K 线输入、Signal、Outcome
    utils.py                  # 已有 K 线工具与桥接
    ...
  kline_bundle/
    base/
      _input.py               # 现有 K 线截面签名
      signal.py               # rKlineBundleSignal
      __init__.py
    utils.py                  # K 线截面工具入口
    return_rank.py
    weighted_index.py
    __init__.py
  orderbook/
    base/                     # 单 symbol 盘口输入和基类
    utils.py
    book_spread.py
    __init__.py
  trade/
    base/                     # 单 symbol 成交输入和基类
    utils.py
    trade_signed_volume.py
    __init__.py
  bundle/
    base/
      _input.py               # step(bundle, *, time=None)
      signal.py               # rBundleSignal
      __init__.py
    utils.py
    __init__.py
```

- `base/` 放输入契约和基类。各类的 schema 声明随其输入层放置；core 不导入这些声明。
- `utils.py` 放该数据类型实际需要的工具，可依赖 base。没有工具时只保留模块说明，不为了目录对称新增空函数、基类或适配器。base 不反向依赖可能导入它的 utils。
- 数据包和根包继续导出常用类。用户正常使用无需知道 `base/` 的内部文件。
- `family` 表示公开的数据契约，不由继承路径或目录名自动推导。现有 `kline/orderbook/trade/kline_bundle` 保留；新通用入口使用 `bundle`。
- 不预建 `trade_bundle`、`orderbook_bundle` 或镜像指标目录；先用具体算子验证通用入口，确有独立稳定契约时再讨论分包。

相较原稿，本轮取消强制删除 `kline_bundle`、删除 `rKlineBundleSignal`、把其 `open_time` 改成 `time`、把其 family 改成 `bundle` 的方案。K 线具体算法和数据身份不变。

内部基础类移入 base 后，`kline_bundle.signal`、`orderbook.signal`、`trade.signal` 的直接导入路径变更；按照此前直接迁移方式，不增加长期转发模块。实施时同步仓内引用并列出迁移表。包级导出不变不代表完全兼容：旧模块路径的序列化实例可能受影响，不能承诺自动迁移。

## 10. 分阶段落地与验收

1. **先整理已存在的输入类型**：按 base/utils 布局迁移 K 线截面、盘口和成交基类，保持签名、family、算法和根级导出。无需等待 schema 完成。
2. **建立最小通用 Bundle**：提供 `step(bundle, *, time=None)`，用非 K 线输入和数值截面验证扩展体验；不建设自动同步或所有数据类型的 Bundle 包装器。
3. **独立实现输入 schema 与必要 core 优化**：按配套设计落实，不将查询代码放进逐条热路径。

每阶段实施前建立 PLAN，实施后记录 OUTCOME，并将计划与结果对应写入 INDEX。本轮仅更新设计，不表示上述阶段已经实施。

验收应覆盖：高频调用代码无需修改、不同 value 格式、空截面推进、成交空序列与未知数据、排名共同时间轴、固定权重和极小权重行为、输入复用不改写历史、发布结果不复用可变容器、批量与逐条一致、类级 schema 查询和错误声明。

现有 `tests/test_kline_bundle.py`、`tests/test_bundle_snapshot.py` 仍引用已移除的历史 API，不能直接视为当前行为的验证依据。实施阶段需明确迁移哪些有效契约；本轮不运行历史测试或示例。

## 11. 三轮查漏补缺

1. **使用体验**：分别走查单 K 线、多 K 线、盘口和成交窗口。K 线无新增包装层；“支持不同格式”未写成“同时拼接多种来源”；不强迫用户认识泛型或 schema 才能调用。
2. **时间与数据正确性**：确认每种输入自有粒度，空截面推进、无成交、缺 symbol、重复最新成交含义不同；基类不从时间标签推断可得性。跨调用历史与已发布输出的引用责任明确。
3. **内部边界与迁移**：高频专用入口和通用入口共享 core 生命周期，参数不强行合并；保留已有缺失行为和 family，schema 无逐条副作用；目录迁移、运行时功能和未来联合输入分别说明，未把设计当作实现。
