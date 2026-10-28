# KlineBundle 横截面设计

创建时间：2026-10-28 07:18 CST
更新时间：2026-10-28 07:36 CST
状态：确定方案，按 [PLAN-027](../dev/PLAN-027-kline-bundle-operator.md) 实施。

> 0.8.0 输入契约补充：Bundle 可直接使用包含 `bars` 的字典，字段映射和可选元信息以[字典输入设计](step-mapping-20261028-overview.md)为准。本稿中的对象构造、时区和时序校验适用于兼容保留的 `KlineBar` / `KlineBundle` 对象；字典输入的时序与截面同步由上游负责。

## 1. 目标

`KlineBundle` 是同一个逻辑时点的多 symbol K 线快照。一个 K 线算子一次接收一个 Bundle，可以一次计算整个截面的均线、排名、相对强度或未来收益。市场事件逐条推进、结果时间位置与 Operator 基类见 [Operator、Signal 与 Outcome 设计](sigma2-operator-signal-outcome-20261028-overview.md)。

主要场景：多 symbol 的逐时点因子、当前截面排序、过去 N 步收益的截面排名、未来 N 步收益、在线事件流、离线逐步重放。横截面结果是主要使用路径；一个算子不需要由用户逐 symbol 调用。

项目按输入数据类型分包：`sigma2/kline/` 关注单 symbol 的 K 线，`sigma2/kline_bundle/` 关注同一时点的多 symbol 截面；`sigma2/core/` 提供共同的算子生命周期和数据 family 基础能力。`KlineBar` 和 `KlineBundle` 的数据模型分别放入对应领域包，截面排名等实现放在 `sigma2/kline_bundle/` 中。

## 2. 快照数据

```python
bar = KlineBar(
    symbol="A", bar_time=timestamp,
    open=100, high=102, low=99, close=101, volume=10,
)
bundle = KlineBundle(
    bar_time=timestamp,
    symbols=("A", "B"),
    interval="1d", time_label="open",
    bars={"A": bar},
    available_at=available_at,
)

bundle.get("A")     # bar
bundle.get("B")     # None，B 的 Bar 缺失
bundle.field("close")  # 与 symbols 顺序一致的一维数组：[101, NaN]
```

- `KlineBar` 为只读值，包含 symbol、`bar_time`、OHLCV 和可选 `available_at`。
- Bundle 的 `symbols` 是固定顺序的完整计算域，`bars` 只包含当前存在的 Bar；已知但缺失的 symbol 用 `None` 表示，未知 symbol 查找报错。所有 Bar 的 symbol 和时间标签与 Bundle 一致。
- 一个流中的 `symbols`、`interval`、`time_label` 固定，`bar_time` 严格递增。symbol 集合变化时开始新运行段；需要连续状态时按新集合重放历史。空时点可以用 `bars={}` 显式输入，算子不会自动补日历。
- 时间使用带时区的 UTC `datetime`，不猜测时区。`bar_time` 是来源声明的开盘或收盘标签；`available_at` 是已确认快照可用的时间，包括缺失判断的放行时间。未知可用时间为 `None`，不能从标签推断。
- 数据来源确认 Bar 已定稿并负责截面放行。真实记录的字段无效可以是 `NaN`，与 Bar 缺失是不同概念；不自动前向填充。

### 固定或变化的 symbol 集合

| 方案 | 优点 | 代价 | 本次选择 |
| --- | --- | --- | --- |
| 固定全集及顺序，缺失用标记 | 每次输出的 symbol 轴稳定，未来结果易回填 | 成员变化要开启新运行段 | 采用 |
| 每个快照改变 symbol 集合 | 天然适合实时上下市 | 历史状态、结果形状和 batch 必须逐行重映射 | 后续按实际需求设计 |

固定全集本身不意味着所有 symbol 每次都有行情；参与排名的集合根据当前有效字段确定。来源不得用未经允许的未来信息确定历史中哪些 symbol 当时可交易。

## 3. Operator、schema 和输出

Bundle 算子构造时显式传入 `symbols`，使 schema、状态和输出轴在第一次运行前就确定。批量接口可从第一个 Bundle 推导，空数据可显式提供 `symbols`。例如：

```python
rank = rKlineBundleRank(symbols=("A", "B"), field="close", return_dict=True)
values = rank.step(bundle)  # {"rank": array([1.0, NaN])}
```

`schema` 直接使用 pyta2 的 `Schema` 和 `Space`，**一个 Space 描述一个 symbol 的输出值**。Bundle 额外提供 symbol 轴：

- 单字段原始输出为 `(S, *space.shape)`；多个字段依 schema 顺序组成 tuple。`return_dict=True` 按 schema key 返回字段数组。`S` 为 symbol 数。
- 例如标量 `Scalar` 对应每次输出 `(S,)`，结果第 i 项属于 `symbols[i]`。空缺和预热按该字段的 `null_value` 填充。
- 也允许显式声明整个截面产生一个标量的算子；此时直接使用普通 pyta2 输出和缓存，不附加 symbol 轴。
- Schema 构造、字段校验、缺失哨兵和 `make_dict_output()` 的语义与 pyta2 一致。时间和 symbol 是结果轴元信息，不作为 schema 字段。

### 输出缓存选择

| 方案 | 优点 | 代价 | 本次选择 |
| --- | --- | --- | --- |
| Space 描述单 symbol 值，symbol 轴由 family 表示 | 直接复用 pyta2 的标量 Space 和每元素缺失值；便于动态查看 symbol 结果 | 缓存要为 symbol 轴提供表视图 | 采用 |
| 把全部 symbol 声明为一个向量 Box | 表达紧凑 | 当前 pyta2 `DequeTable` 不保存数组字段，`Box.contains()` 也无法将部分 NaN 向量当作有效值 | 本次不采用 |

横截面输出缓存使用 pyta2 `DequeTable` 将每个字段的 symbol 元素分别存储，再对调用者呈现字段数组。`outputs[key]` 的形状是 `(缓存步数, S, *space.shape)`；`outputs[-1]` 返回当前字段数组，`latest` 与它一致。标量算子直接使用 pyta2 `DequeTable`。默认 `buffer_size=1`，`0/None` 关闭，`-1` 无限，正数表示最近 N 步。转换和 dtype 缺失行为继续使用 pyta2 表工具，例如布尔 `None` 的现有限制不会由 sigma2 静默改变。

`step()` 返回原始计算结果；缓存保存按 dtype 转换的副本。需要保留结果身份时，收集器应一起记录数据流、`symbols`、算子 `full_name`、`output_key`、结果所属位置及实际可用时间。

## 4. 时间、缺失与排名

- Bundle 每输入一次，实例 `g_index` 推进一次。Signal 的 `result_index` 是当前快照位置；固定未来期为 H 的 Outcome 使用 `g_index-H`。一项未来结果的所有 symbol 对应同一个锚点。
- `n_forward=H` 是 H 个输入快照，不自动等于 H 个自然日。按特定交易日历补齐时点由上游显式生成。
- 各算子声明缺失和预热规则。与当前 pyta2 的未来收益和变动一致，这两个 Outcome 要求锚点及全部未来区间对应字段均有效；缺失不借用前价。排名忽略当前输入无效的 symbol，并在其位置输出缺失值；有效值相同采用平均名次，升序默认从 1 开始。
- 过去 N 步收益排名以共同快照为时间轴，以两个端点的有效收盘价计算收益并对有效收益排名。中间快照不会被跳过，也不会在缺失时自动补价格。
- 构造输入之前应确认何时可以判定缺失。记录结果所属锚点和可用时间；未来结果回填到锚点并不表示它在锚点时已知。

## 5. 批量与状态

批量接口依次执行同一个 `step(bundle)`：Signal 结果写入当前行，Outcome 成熟结果写入 `result_index`，最后 H 行填充缺失。`dict` 输出字段数组为 `(T, S, *space.shape)`，元信息保存 `symbols`、各行时间、结果产生的行情时点和输入数据最早齐备时间；表格输出以 `(bar_time, symbol)` 对齐。输入齐备时间不包含计算和发布延迟，不等于结果的实际可用时间。空输入返回与 schema、显式 symbol 轴匹配的空数组。

单 K 线 family 的 `rKlineSignal` / `rKlineOutcome` 接收 `KlineBar`；Bundle family 的 `rKlineBundleSignal` / `rKlineBundleOutcome` 接收 `KlineBundle`。已有单 symbol 算子可通过 `rKlineBundleMapSignal` / `rKlineBundleMapOutcome` 复用：适配器为各 symbol 持有独立子算子，收到缺失 Bar 时传入显式的缺失占位并推进共同时间。横截面排名直接继承 Bundle family，不重复进行逐 symbol 排名。

每个算子有独立状态。复用 pyta2 rolling 指标时，单 K 线算子保存算法所需窗口。不是所有 pyta2 指标都支持有限前缀：内置适配针对具体指标明确保留量，通用适配器要求调用者显式提供历史长度。当前 pyta2 KAMA 遇到无效窗口可能让递推状态长期无效，sigma2 的内置适配会重置它并等待有效窗口；其他指标按自身缺失规则处理。pyta2 尚未完成迁移的 ATR、KDJ 和未来路径计算由 sigma2 使用有界状态实现，并说明其公式和缺失规则。

输入验证在状态推进前进行；计算、转换或缓存失败后实例进入 faulted 状态，`reset()` 成功后必须从已确认输入序列开头重放。输入窗口、输出缓存和持久化数据源的所有权分别管理。

## 6. 三轮查漏补缺

1. **调用与命名**：`step(bundle)` 一次接收完整截面；`rank` 等结果一次覆盖全部 symbol；训练 target 概念不进入核心。
2. **对齐与缺失**：symbol 轴稳定；没有 Bar、字段 NaN、未成熟未来结果及实际可用时间分别表示；未来期按共同快照计数。
3. **schema 与资源**：每 symbol 的 Space 沿用 pyta2；跨 symbol 缓存显式拆分为标量列，输入窗口不由 `min_periods` 自动推断；成员变化、错误及重放有明确边界。
