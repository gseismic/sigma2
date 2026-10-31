# core 与单 K 线 MA 的精简设计

> 生命周期以[算子单向推进设计](operator-single-pass-20261031-overview.md)为准；本文保留当时的实现记录。

- 创建时间：2026-10-29 16:21 CST
- 更新时间：2026-10-30 06:00 CST
- 状态：按本轮范围实施；不要求兼容旧接口。

## 1. 目标与范围

本轮只实施通用 `sigma2/core`、单 K 线 Signal 输入及 `sigma2/kline/trend/ma.py` 直接涉及的代码。Bundle、其他 K 线指标、订单簿、成交、Outcome 和通用 batch 暂不迁移；它们沿用旧接口，受 core 和 K 线基类变更影响的调用需要在后续工作中适配。本轮不能通过旧输入类或旧字段映射为新 MA 维持兼容。

后续已迁移其他单 K 线算子、订单簿和成交，固定 K 线输入由 Signal 与 Outcome 共用；旧 Bundle 和 batch 已归档，当前范围见 [数据类型迁移设计](data-families-step-20261030-overview.md)与 [遗留依赖清理](retire-legacy-batch-20261030-overview.md)。

sigma2 复用 pyta2 的指标和 schema；用户从固定字段调用 `step`，逐条结果始终是字典。core 源码不导入 K 线等数据包，导入 `sigma2.core` 时也不应因根包聚合而加载数据包。

## 2. 主要场景

1. 逐根输入标准 OHLCV，MA 返回 `{"ma": 值}`。
2. 最后一根 K 线多次更新，直到 `is_closed=True`，结果与最终序列重放一致。
3. MA 通过构造参数选择 `close` 或 `volume`，元信息随参数报告对应的 `used_fields`。
4. 整根 K 线缺失或可选 volume 缺失时，正常推进时间并将缺失数值传给 pyta2。
5. 用户直接导入 core，不触发 sigma2 数据模块加载。
6. 简单自定义 Signal 只实现返回字典的 `forward`，无需声明 schema 或实现重置方法。
7. 同一根未结束 K 线更新后确认，或者发现时间与结束状态不一致并提示上游恢复。

## 3. 方案比较

| 问题 | 方案 | 优点 | 代价与选择 |
| --- | --- | --- | --- |
| K 线输入 | 字典、对象与字段映射 | 可直接消费多种数据源 | 需要视图和兼容分支；本轮新接口不采用。 |
| K 线输入 | 固定参数 | 签名明确，代码直观 | 数据源需先整理字段；采用。 |
| 单步结果 | 单值、tuple、字典可选 | 对部分调用稍短 | 调用方需判断结果类型；不采用。 |
| 单步结果 | 始终返回 schema 键的字典 | 单输出和多输出一致 | 复用 pyta2 原始结果需要转换；采用。 |
| 计算钩子 | 允许单值或 tuple，由 core 转换 | 旧子类改动较少 | core 要维护转换规则；不采用。 |
| 计算钩子 | `forward` 直接返回字典 | core 只检查输出是否符合 schema | 各算子自己组织结果；采用。 |
| 未结束观测 | 重放完整历史 | 不需复制状态 | 成本和内存随历史增长；不采用。 |
| 未结束观测 | 保存观测前状态并重复恢复 | 可正确重算递推指标 | 需要复制持有状态；采用。 |
| 结束状态 | 依赖 `close_time` 判断 | 可记录预定的结束时间 | 时间字段本身不能确认收到的是最终行情；不采用。 |
| 结束状态 | 调用方传 `is_closed` | 明确区分更新和确认 | 上游必须正确标记结束；采用。 |
| 字段描述 | 运行时检查必需字段 | 可提前报错 | 重复固定输入协议并增加逐条开销；不采用。 |
| 字段描述 | 参数化 `used_fields` 元信息 | 说明公式实际使用的行情字段 | 由实现者维护；采用，不用于检查或计算分支。 |
| 字段声明 | 子类属性动态生成 `used_fields` | 字段改变时可动态更新 | 每个子类都要增加属性；目前字段在初始化后固定，不采用。 |
| 字段声明 | 初始化时将 `used_fields` 传给 core | core 统一保存元信息，子类只声明自身字段 | 字段配置后续若可变需同步元信息；采用。 |
| 输出描述 | 每个算子都必须声明 schema | 类型和输出字段在计算前明确 | 简单自定义 Signal 需要额外样板；不采用。 |
| 输出描述 | schema 可选，缺省时按首次结果确定字段 | 简单自定义 Signal 只实现 `forward` | 缺省时没有类型 schema，缓存使用 object 类型；采用。 |
| 结束和标识 | 只使用观测标识推断是否结束 | 少传一个状态 | 无法明确确认最终值，也不能发现遗漏结束消息；不采用。 |
| 结束和标识 | 结束标志控制确认，并用标识检查一致性 | 观测标识与结束状态可交叉检查 | 上游遗漏确认时需要先恢复；采用。 |
| 状态重置 | 子类分别实现重置钩子 | 可手工控制对象重置 | 每个简单子类都要实现，且易遗漏状态；不采用。 |
| 状态重置 | core 在首次计算前保存初始状态并自动恢复 | 无状态 Signal 不必编写重置方法 | 可变计算状态需集中且可深复制；采用。 |

## 4. 接口与语义

```python
step(open, high, low, close, volume=None, *,
     open_time=None, is_closed=True, is_missing=False) -> dict
```

- 一个实例消费一个 symbol 的 K 线流。OHLC 必须由调用方提供，volume 可以为 None；时间和状态是关键字参数。
- 不逐条检查 OHLCV 必需字段，也不对每个行情字段做 float 转换；数据源保证输入格式。`is_closed` 和 `is_missing` 按对话代码检查为布尔值，避免把其他值误当成状态；Python 函数签名本身约束传参。
- `is_missing=True` 表示整根缺失，其 OHLCV 按缺失数值送入指标。`volume=None` 在使用 volume 的 MA 中按缺失数值处理，不影响使用其他字段的 MA。
- `is_closed=False` 首次调用分配一个索引并保存观测前状态。相同 `open_time` 的后续更新恢复状态、重算并替换最后一条结果；`is_closed=True` 确认同一索引并释放快照。时间可为 None，此时上游保证顺序。
- 最近一次观测的 `open_time` 已知时，未结束的观测收到不同时间会报错；已结束的观测收到相同时间也会报错。上游需要补齐漏掉的结束消息、过滤重复消息；历史数据修订时需重置并重放。当前输入或当前观测的时间缺失时，无法检查本次是否属于同一观测，仅按结束状态推进或重算；未结束观测中已知的时间会保留，供其后续更新核对。不同时间也不检查其先后顺序。
- MA 始终返回 `{"ma": 值}`。MA 的唯一算法参数为 `n`，类型支持 SMA、EMA、WMA、HMA、DEMA、TEMA、ZLEMA；不提供 `ma_kwargs`。
- 固定的 `step` 签名本身描述可接收的输入，不再额外维护重复的 `step_input_keys` 元信息。
- `used_fields` 只描述实例计算使用的行情字段：`field="close"` 时为 `("close",)`，`field="volume"` 时为 `("volume",)`。算子根据实例参数通过父类构造函数传入字段，core 保存并组装 `meta_info`，不使用该信息进行运行时检查。默认为 `None`，表示未声明；空元组表示已声明不使用行情字段。通用控制字段不计入。
- `used_fields` 与计算配置在构造时确定；如果将来允许修改使用的字段，算子作者须同步更新元信息。简单自定义 Signal 可以省略该参数，仍然只需实现 `forward`。
- core 默认创建空的 `_state`，不需要传入状态。所有可变计算状态必须放在其中；使用时也从 `_state` 读取，不能保留会绕过恢复的状态别名。core 首次计算前保存初始状态，`reset()` 自动恢复；在首次计算前重置时保留子类已经配置好的初始状态。MA 的 pyta2 指标和输入窗口一起恢复。计算失败锁定实例，重置后重放。
- core 的公开 `step` 是抽象接口，由数据类型定义固定签名并调用 `_step`；误调用抽象方法本身会抛出 `NotImplementedError`。core 内部 `_step` 统一负责观测标识、结束状态和状态快照，选择推进或重算；K 线层只整理输入并传入 `open_time` 和 `is_closed`。`rSignal` 将 `n_forward` 固定为 0。
- `forward` 必须返回字典。指定 schema 时，输出字段必须与 schema 一致；未指定时，首次结果确定字段，后续结果必须保持一致，`schema` 保持 `None`，输出缓存使用 object 类型以免根据首值错误推断类型。重置保留已确定的字段；core 不将单值或 tuple 转换为字典。
- `n_backward`、`n_forward` 和输出缓存容量在构造时指定，运行中只读；容量 `0` 关闭缓存，`-1` 无限，正数保留最近 N 条。
- 指定 schema 时，可空字段和多维输出使用 object 列；在线和批量缓存均保留对应的缺失值和数组。

调用示例：

```python
from sigma2.kline import rKlineMA

ma = rKlineMA(2, ma_type="EMA", field="close")
ma.step(100, 101, 99, 100, open_time=1)
preview = ma.step(100, 109, 99, 108, open_time=2, is_closed=False)
confirmed = ma.step(100, 111, 99, 110, open_time=2, is_closed=True)
print(preview["ma"], confirmed["ma"])  # 104.0 105.0
print(ma.meta_info["used_fields"])  # ('close',)
```

core 的推进逻辑分两条路径：新观测先按需保存状态、再推进索引和计算；更新未结束观测时恢复原始快照、重算并替换缓存尾行，不再推进索引。最终确认后删除快照。这样不用保存完整输入历史，也不会把多次盘中更新当成多根 K 线。

`_state_before_pending` 保存尚未确认的观测首次计算之前的状态；为 `None` 时没有等待确认的观测。具体信号实现 `forward` 计算结果，调用方通过 `step` 推进，避免直接调用 `forward` 而跳过生命周期管理。

简单自定义信号只需要重载 `forward`：

```python
from sigma2.kline import rKlineSignal

class Body(rKlineSignal):
    def forward(self, open, high, low, close, volume=None, *,
                open_time=None, is_closed=True, is_missing=False):
        return {"body": close - open}

body = Body()
body.step(100, 105, 99, 103, open_time=1)  # {"body": 3}
```

需要类型约束、预热长度或可变计算状态的信号，可以分别传入 schema、设置 `n_backward`、在 `_state` 中存放计算状态。

## 5. 迁移边界

- MA 和新的单 K 线 Signal 不再依赖 `_KlineInput`、`FieldView`、`KlineBar` 或字段映射。旧文件仍被未迁移的 Outcome、Bundle、batch 等引用，本轮不删除或修改它们。
- 通用 core 的 `step` 返回字典；旧调用方可能仍假定标量、tuple 或旧参数。本轮不适配这些调用方，结果文件需明确列出影响。
- 订单簿和成交的旧 Signal 仍通过 `super().step(...)` 调用原先的默认实现；core 的 `step` 已成为抽象接口，因此这些 family 需要后续迁移。
- 只删除 MA 路径中的复杂继承和 KAMA 特判；其他指标的实现和其 KAMA 特判暂不修改。
- MA 原有批量入口依赖尚未迁移的通用 batch；本轮不提供占位的 `KlineMA` 批量函数，不重构通用 batch。后续 PLAN-040 恢复 MA 批量入口，使用固定字段逐条重放，详见 `signal-step-batch-20261030-overview.md`。
- 保留根包的常用名称并按需加载，以保证 core 导入链不触发数据 family；仅调整与 core 和 MA 导入直接相关的聚合代码。

## 6. 三轮检查

1. **接口与缺失**：固定签名和仅元信息的 `used_fields` 不触发字段检查；volume 缺失不会影响 close MA。
2. **状态与结果**：同一观测每次从同一快照重算；索引和缓存不重复推进；MA 的窗口和 pyta2 内部状态均在快照内。无 schema 时首值不能决定后续数值精度。
3. **职责与范围**：core 不引用数据 family，统一管理观测标识、结束状态和快照；MA 自己选择字段并调用 pyta2；其他未迁移入口和代码不扩展实施范围。

状态快照依赖所含对象正确支持深复制；其他算子若需要盘中修订，必须先将全部可变计算状态纳入 `_state`。实时复制成本需要实际测量。

当 `open_time` 缺省时，算子无法自行区分不同 K 线，上游必须先确认上一根再传下一根。已经确认的历史 K 线若被修订，需重置并从可靠数据重放；本设计仅支持未结束的最后一根。实例不保证并发或重入安全。`used_fields` 的准确性由算子作者负责维护。
