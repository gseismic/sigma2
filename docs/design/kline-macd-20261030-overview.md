# 单 K 线 MACD 精简设计

> 生命周期以[算子单向推进设计](operator-single-pass-20261031-overview.md)为准；本文保留当时的实现记录。

- 创建时间：2026-10-30 05:44 CST
- 范围：`rKlineMACD`、直接导出和使用说明；不迁移其他指标、数据类型或通用 batch。
- 依据：`docs/design/kline-step-core-20261029-overview.md` 和 `rKlineMA` 的实现方式。

## 目标与场景

1. 以固定 K 线字段逐条计算 MACD，输出 `dif`、`dea`、`macd` 字典。
2. 最后一根未结束的 K 线可以反复更新，结束时确认结果。
3. 通过构造参数选择 `close` 等行情字段，元信息中的 `used_fields` 与实例字段一致。
4. 使用 `volume` 且它为 None、或整根 K 线缺失时，将缺失值交给 pyta2 处理。
5. 用户可以获取指标参数、公式名、预热长度和输出缓存。
6. 调用 `reset()` 后可以从相同初始状态重放。

## 选择

| 选择 | 优点 | 决定 |
| --- | --- | --- |
| 沿用 `_rKlineIndicatorFactor` | 保留旧指标共享逻辑 | 依赖旧窗口、输入与 KAMA 处理；不采用。 |
| 类似 MA 直接组合 pyta2 MACD | 仅保存一个指标与所选字段窗口，生命周期由 core 管理 | 采用。 |
| pyta2 返回 tuple 后由 sigma2 映射字段 | 输出转换受 sigma2 控制 | 重复维护输出顺序；不采用。 |
| pyta2 设置 `return_dict=True` | 直接获得与自身 schema 一致的字典 | 采用，sigma2 仍通过 core 检查输出键。 |
| MACD 另行实现批量接口 | 可直接消费一批数据 | 通用 batch 尚未适配，当前不提供；后续统一迁移。 |

## 接口与职责

```python
rKlineMACD(fast=12, slow=26, signal=9, *, field="close", buffer_size=1)
step(open, high, low, close, volume=None, *,
     open_time=None, is_closed=True, is_missing=False) -> dict
```

- `fast`、`slow`、`signal` 分别为快线、慢线与信号线周期，沿用常见参数顺序；pyta2 构造时明确映射为 `n2`、`n1`、`n3`。周期及 `slow > fast` 由 pyta2 校验。
- `field` 支持 `open`、`high`、`low`、`close`、`volume`，仅选择其中一个字段计算；构造时向 core 传入 `used_fields=(field,)`，只作为元信息。
- `rKlineSignal` 负责固定输入和缺失 K 线处理；core 负责观测标识、末根更新、输出缓存、状态快照与重置。无须另设重置钩子。
- `_state` 只包含一个 pyta2 `rMACD` 和一个长度为其 `min_periods` 的所选字段窗口；两者一起深复制。指标的三个 EMA 和 DIF 缓存在该指标内部。
- 使用 pyta2 的输出 schema、`n_backward` 和公式名；其当前定义的 `n_backward = slow + signal - 2`，各输出是否已预热由 pyta2 判断。
- 输出恒为 `{"dif": ..., "dea": ..., "macd": ...}`；缺失值和后续恢复完全由 pyta2 处理，sigma2 不增加算法特判。
- 原 `KlineMACD` 依赖未迁移的通用 batch，本轮与 MA 一样移除该入口及直接导出。后续 PLAN-040 通过固定字段逐条重放恢复批量入口，详见 `signal-step-batch-20261030-overview.md`。

## 三轮检查

1. **接口**：固定输入与 MA 一致，周期顺序和 pyta2 的 `n1`、`n2`、`n3` 映射明确；字段元信息与实例参数一致。
2. **结果与状态**：直接使用 pyta2 字典和 schema，保存实际会变化的指标及输入窗口；预览更新和确认由 core 从同一快照重算。
3. **边界**：缺失处理由 pyta2 决定；时间缺省时上游保证顺序；对象深复制能力和成本需要后续运行验证；其他未迁移模块不在本轮范围。
