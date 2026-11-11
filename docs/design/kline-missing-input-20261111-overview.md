# 单 K 线输入透传与缺失值约定

- 创建时间：2026-11-11 21:43 CST
- 状态：按本设计实施。
- 范围：单 K 线基类的 `step()` 输入、缺失标记和基类导出。

## 目标与使用场景

按极简原则，单 K 线基类只定义输入签名并转交通用生命周期，输入格式和缺失字段由上游提供。`is_missing` 保留为可传给自定义算子的标记，不由基类校验或改变输入字段。

| 场景 | 约定 |
| --- | --- |
| 处理完整 K 线 | OHLCV 按原值传给 `forward()`，结果由具体算子决定。 |
| 处理整根缺失 K 线 | 上游为需要表达缺失的字段传入 NaN，可同时设置 `is_missing=True`。 |
| 设置 `is_missing=True` 但提供有效价格 | 价格按原值传入；现有内置单 K 线算子不依据该标记自动忽略价格。 |
| 自定义 Signal 或 Outcome 使用缺失标记 | 自定义 `forward()` 可按自身约定解释原样传入的 `is_missing`。 |
| 未提供 `volume` | 签名保留 `None` 默认值；具体算子使用成交量时延续其现有的缺失处理。 |
| 导入 K 线基类 | `from sigma2.kline import rKlineSignal, rKlineOutcome`，也可从 `sigma2.kline.base` 导入。 |

## 方案比较

| 方案 | 行为 | 决定 |
| --- | --- | --- |
| 保留现状 | 基类校验 `is_missing` 类型，标记缺失时将 OHLCV 全部改为 NaN | 增加隐式输入修改，与本次极简要求不符。 |
| 基类直接透传 | 删除类型检查及自动替换；上游提供字段值，自定义算子可自行使用标记 | 按用户要求采用。 |
| 将自动替换移到每个算子 | 在各 `forward()` 重复根据标记替换字段 | 继续隐式改变输入且产生重复，不采用。 |

## 调用链与接口

`rKlineSignal` 的方法解析顺序是 `rKlineSignal -> _KlineStep -> rSignal -> rOperator`；`rKlineOutcome` 对应 `rKlineOutcome -> _KlineStep -> rOutcome -> rOperator`。由于 `rSignal` 和 `rOutcome` 没有覆盖 `step()`，`_KlineStep` 的 `super().step()` 最终调用 `rOperator.step()`。该调用保留统一的索引推进、`forward()`、输出检查、缓存和失败锁定，适合当前协作式多重继承。

`sigma2.kline.__init__` 的懒加载映射已包含 `rKlineSignal` 和 `rKlineOutcome`，`__all__` 由该映射生成；已有包级导出满足需求，无须重复添加导入。

## 三轮检查

1. **调用与导出**：不改变 `step()` 参数及其转发顺序；两类 K 线基类继续通过同一输入层进入 core，已有包级导出保留。
2. **缺失语义**：不再把 `is_missing=True` 等同于自动改写数据。现有内置单 K 线算子未消费该标记，调用方应传递需要的 NaN；具体算法及 pyta2 仍决定 NaN 如何影响结果。
3. **状态与兼容**：非布尔标记不再由入口提前拒绝；如自定义 `forward()` 因输入出错，则按 core 规则锁定实例。原先依赖标记自动屏蔽有效价格的调用方必须改为提供 NaN。
