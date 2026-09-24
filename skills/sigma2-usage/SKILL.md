---
name: sigma2-usage
description: 在本仓库使用或扩展 sigma2 信号与因子时使用，涵盖在线 step/update_last、批量 replay、因子身份和新增 Signal 的实现约定。
---

# sigma2 使用与扩展

帮助用户正确调用 sigma2 的在线、批量和 family API；用户要新增信号或因子时，按本仓库当前实现约定扩展。

## 先确认当前 API

- 先看仓库根目录 `README.md` 和 `sigma2/__init__.py`。需要新增 K 线因子时，再读 `docs/design/kline-factor-20260922-template.md`；需要组合状态或自定义 family 时，读 `docs/design/sigma2-20260922-v5.md` 的相关章节。
- 以当前源码和导出为准。仓库设计文档包含历史版本章节；当前 K 线名称是 `rKlineX` / `KlineX`，不要从旧章节复制已移除的 `rMA` / `MA` 等名称。
- sigma2 管理市场 family 输入、字段绑定和 Signal 生命周期；pyta2 提供可复用的 rolling 指标。避免为 sigma2 创建 pyta2 指标名称的镜像目录或短名称。

## 在线调用

在线每次输入一条观测，使用 `step()` 推进：

```python
from sigma2 import rKlineRSI

signal = rKlineRSI(14, field="close")
value = signal.step(
    open=100.0,
    high=103.0,
    low=99.0,
    close=102.0,
    volume=1200.0,
)
```

如果同一条最新观测被行情源修订，使用与 `step()` 相同字段调用 `update_last()`。它会从当前观测之前的检查点重算，不增加 `g_index` 或输出行；连续修订也是安全的。`update_last()` 只改最后一条观测，不支持修改历史任意位置。

每个 Signal 实例只服务一条输入流，不要跨 symbol、周期或线程共享。计算失败后实例进入 faulted 状态；调用 `reset()` 并重放已确认的观测后再继续。不要直接调用 `forward()` 推进生命周期。

## 批量调用

`KlineX` 接受以 OHLCV 列为基础的列式对象，例如普通 dict 或 pandas DataFrame。必需列必须是一维且长度一致；默认输出 `dict[str, numpy.ndarray]`，键是训练用的因子名。

```python
from sigma2 import KlineMA

data = {
    "open": opens,
    "high": highs,
    "low": lows,
    "close": closes,
    "volume": volumes,
}
features = KlineMA(data, 20, ma_type="EMA", field="close")
```

`return_type` 可选 `"dict"`、`"tuple"`、`"list"`、`"dataframe"` / `"pd.dataframe"`、`"pl.dataframe"`；后两类分别需要 pandas 或 polars。需要元信息时传 `return_meta_info=True`，返回 `(result, meta_info)`。batch 接口会逐行调用同一个 Signal 的 `step()`；用户需要在线和离线一致性时，应复用配对的 `rKlineX` / `KlineX`，不要另写批量公式。

## 因子身份与 pyta2

- `full_name` 是人可读、可复现的因子身份；单输出的 `factor_names` 等于 `[full_name]`，多输出按 `full_name.output_key` 展开。
- `output_keys` / schema key 是逐条输出结构，不替代训练列名。多输出 Signal 在 `return_dict=True` 时仍按 schema key 返回字典。
- 同时使用两个库时分别按 family 名导入，例如 `from pyta2 import rRSI, RSI` 与 `from sigma2 import rKlineRSI, KlineRSI`。pyta2 primitive 处理指标本身；sigma2 Signal 绑定市场输入并管理生命周期。需要将通用 pyta2 rolling 指标接入 K 线时，查看 `pyta2_signal()`；独立、稳定的公开因子优先使用具名 `rKlineX` / `KlineX` API。
- 依赖未来 K 线的数据是 target，不是可用于当下决策的 causal feature。现有未来目标放在 `sigma2.kline.target`，并不支持 `update_last()`；不要把它们混入正向特征 Signal。

## 新增 Signal

当用户要新增 Signal/因子时，先阅读 [新增信号指南](references/add-signals.md)。该指南覆盖目录选择、pyta2 指标复用、结构化 family Signal、自有状态、导出、身份命名和契约测试。若任务是在重新设计公共接口而非沿用既有契约，另按仓库说明使用 `api-design-zh` skill。
