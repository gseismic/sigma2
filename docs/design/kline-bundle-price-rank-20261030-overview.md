# K 线截面与价格排名设计

> 2026-10-30：用户要求将价格排名改为收益率排名；现行接口和语义见 [K 线截面收益率排名设计](kline-bundle-return-rank-20261030-overview.md)。本文保留当时的设计记录。

## 目标与场景

本次只重建 K 线截面 Signal 的固定输入和当前价格排名。常见场景包括：对多个 symbol 的收盘价排名、改用开盘或最高最低价、按相反方向排名、处理相同价格、处理缺失 K 线、处理空截面，以及逐时点重放。后续按 symbol 复用单 K 线算子或计算未来结果时再设计。

## 方案比较

| 问题 | 方案 | 选择 |
| --- | --- | --- |
| 输入 | 在基类重建对象、字段映射和逐字段校验 | 调用方已有固定数据格式，额外包装会增加复杂度；不采用。 |
| 输入 | `step(bundle, *, open_time=None, has_missing=False)` | 沿用讨论的固定字段；数据类型层只转交 core，采用。 |
| symbol 轴 | 构造时指定全集，返回位置数组 | 需要维护固定顺序和额外缓存适配；不作为当前简单排名的要求。 |
| symbol 轴 | 每次直接返回当前输入 symbol 到排名的映射 | 结果自带 symbol，可自然处理 symbol 变化，采用。 |
| 输出 | 直接将 symbol 用作最外层键 | symbol 集合变化时，core 的固定输出字段会变化；不采用。 |
| 输出 | `{"rank": {symbol: rank}}` | 最外层 schema 键稳定，内层明确对应每个 symbol，采用。 |
| 缓存 | 自建 symbol 轴表、展开数组 | 新增复杂度且无固定全集；不采用。 |
| 缓存 | 使用 core 未声明 schema 时的 object 列 | 复用现有生命周期并保存每个时点的 symbol 字典，采用。 |

## 接口和语义

- `rKlineBundleSignal.step(bundle, *, open_time=None, has_missing=False)` 每次处理一个确认的截面，直接把三个字段交给 `_step`；自定义 Signal 只需实现 `forward`。`open_time` 作为 core 的观测标识；提供时连续重复的标识被视为重复提交并报错，省略时由调用方保证顺序。
- `bundle` 是 `{symbol: {open, high, low, close, volume?, is_missing?}}`。上游负责字段格式和时间一致性；`has_missing` 是传给 `forward` 的截面信息，不推断缺少哪些 symbol。价格排名始终读取每个 Bar 的 `is_missing`，不以 `has_missing` 决定是否检查。
- `rKlineBundleRank(field="close", ascending=True)` 默认对收盘价从低到高排名，最小值为 1；支持 open/high/low/close，`ascending=False` 为降序。相同价格取平均名次，例如第 1、2 名并列时均为 1.5。`used_fields=(field,)` 从实例配置传给基类，仅作元信息。
- 输出 `{"rank": {symbol: rank}}`。只包含输入的 symbol；输入中标记 `is_missing=True` 或价格非有限值的 symbol 对应 NaN，不参与排序。没有提供的 symbol 无法推断，须由上游显式提供缺失 Bar。空 Bundle 返回 `{"rank": {}}`。
- 名次是浮点数，以支持并列平均值；排序为 `O(S log S)`，临时空间为 `O(S)`。无历史计算状态，core 仍负责索引、缓存和重置。输出字典与 object 缓存共享引用，调用方应视已返回的嵌套结果为只读。
- `KlineBundleRank` 用 `forward_step_apply` 重放固定字段字典序列；`rank` 是每行保存一个 symbol 字典的 object 列，不假装存在固定二维 symbol 轴。由于未声明 schema，空输入返回空字典；非空输入从首个结果确定 `rank` 字段。

## 三轮检查

1. 用户可直接按 symbol 查排名，不需要知道 symbol 位置；固定输入没有引入额外封装、字段映射或必需字段检查。
2. 每条快照是已确认观测；core 处理索引和缓存。缺失和并列仅影响当前快照，不沿用上一个时点的价格或排名。
3. 动态 symbol 的字典不能用单个浮点 Space 真实描述，因此省略 schema 并使用 object 列；空输入与对象引用语义需明确。未来 Bundle 若需要固定轴、未结束快照或数组缓存，再单独设计，不假设本次已覆盖。
