# 多 symbol 截面字典结构

创建时间：2026-10-28 15:55 CST
状态：按用户确认的结构实施；现阶段不考虑兼容性。

## 背景与选择

一个 `step()` 处理同一逻辑时点的多 symbol K 线，既要支持截面计算，也要容纳可选的时间和其他快照字段。

| 结构 | 优点 | 取舍 |
| --- | --- | --- |
| `{symbol: bar, ...}` | 简短 | symbol 和元信息处于同一命名空间，难以区分 |
| `{"open_time": t, "bundle": {symbol: bar}, ...}` | 截面和元信息明确分开，符合用户提出的结构 | 多一层字典 |

采用第二种，`open_time` 可省略，`bundle` 必需。多余字段允许保留，OHLC 必需及其他字段由算子决定的规则不变。截面和每个 Bar 均使用 `Mapping` 协议，不要求构造特定数据类；既有固定字段数据类与这一协议不一致，移除它的公开入口和专用处理。

```python
snapshot = {
    "open_time": 1,
    "bundle": {
        "BTC": {"open": 100, "high": 102, "low": 99, "close": 101},
        "ETH": {"open": 200, "high": 202, "low": 198, "close": 201},
    },
}
value = rKlineBundleRank(symbols=("BTC", "ETH")).step(snapshot)
```

## 字段、时间和映射

- `bundle` 是 symbol 到 Bar 的映射；`symbols`、`available_at` 等仍可作为顶层字段。固定 symbol 轴、缺失、校验和结果对齐规则不变。
- Bundle 字典默认以 `open_time` 作为行情时间；它不是可用时间。元信息 `bar_times` / `last_bar_time` 和表格索引使用通用名称 `bar_time`，便于与单 K 线批量结果统一。无时间或部分时间缺失时，表格使用 `g_index`。
- `bundle_key_map` 的方向仍是逻辑字段到原始输入字段，例如 `{"bundle": "klines", "open_time": "date"}`；显式映射优先，不回退到同名字段，也不做链式映射。`key_map` 仍只作用于 Bar 内部。
- 字典视图中 `snapshot["bundle"]` 得到已校验并完成字段映射的 Bar；额外字段可读取。`bars` 和 `bar_time` 仅是普通额外字段，不会触发自动识别或替代默认字段；需要使用其他源字段时，显式配置 `bundle_key_map`。
- 字典中的时间顺序、周期、截面同步和何时可用由数据源负责，算子按输入顺序推进。符号全集、已出现 Bar 的必需字段和 Bar 中显式提供的 symbol 仍在推进前校验。

## 三轮检查

1. **使用与边界**：默认调用不需要映射；`open_time` 不变为必需；空截面与缺失 symbol 的行为不变；快照扩展字段与 symbol 名称处于不同层。
2. **映射与字段**：不把额外的 `bars`、`bar_time` 当作标准字段；显式映射始终优先，不做链式映射；Bar 与截面使用独立映射作用域。
3. **结果与生命周期**：单步和 batch 采用相同快照解析，未来结果仍按 `result_index` 回填；输入缺字段在状态推进前报错；可用时间不从 `open_time` 推断；映射子算子的缺失占位继承同一行情时间。

本设计更新 `docs/design/step-mapping-20261028-overview.md` 中的 Bundle 字段选择；其单 K 线及其他契约仍适用。
