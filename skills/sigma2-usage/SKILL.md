---
name: sigma2-usage
description: 当用户询问如何安装或使用 sigma2、计算 K 线/盘口/成交因子、处理在线 step/update_last 与批量结果、理解因子列名和未来 target，或要在本仓库新增 Signal/因子时使用。给出与当前源码一致的可运行示例及扩展步骤。
---

# sigma2 使用与扩展

帮助用户正确调用现有公共 API；需要扩展时，遵循当前 family、生命周期和因子身份契约。

## 先定位任务和当前实现

1. 先读仓库根目录 `README.md`、`sigma2/__init__.py`，再读对应示例和目标类源码。源码与导出优先于历史设计文档。
2. 如果是新增 K 线因子，读 `docs/design/kline-factor-20260922-template.md`；如果是自定义状态、组合或新 family，读 [新增信号指南](references/add-signals.md) 和总设计中相关章节。
3. 当前版本为 0.4.0。K 线公共名称是 `rKlineX` / `KlineX`；不要引用已删除的 `rMA` / `MA` 等短名称或旧模块路径。

| 用户需求 | 先看示例 |
| --- | --- |
| 离线计算 MA、MACD 或理解返回列 | [K 线批量](../../examples/01_kline_batch.py) |
| 实时推进、最后一根修订、继续输入 | [K 线在线](../../examples/02_kline_stream.py) |
| 盘口快照或逐笔成交 | [市场事件](../../examples/03_market_events.py) |
| 未来收益等监督目标 | [未来目标](../../examples/04_future_target.py) |
| 临时复用 pyta2 rolling 指标 | [pyta2 桥接](../../examples/05_pyta2_bridge.py) |
| 自定义带递推状态的 Signal | [自定义 Signal](../../examples/06_custom_signal.py) |
| 无 pyta2 指标的 K 线两级均值模板 | [两级均值](../../examples/07_mean_of_mean.py) |

## 回答使用问题

- 给用户能直接运行的代码：定义全部输入变量，使用当前导出的名称，K 线传完整 `open/high/low/close/volume`。说明窗口未满时可能返回 `NaN`。
- 在线用 `step()` 处理新观测；`update_last()` 只修订最近一次 `step()` 的观测，不能任意改历史。重复修订不推进 `g_index`。计算失败后 `reset()` 并重放已确认输入；每条 symbol/周期输入流使用独立实例。
- 批量调用具名 `KlineX(data, ...)`，或对自定义 Signal 使用 `forward_signal_apply(data, SignalClass, ...)`。列式输入的必需键由 `step_input_keys` 决定，必需列须一维且等长。默认得到以 `factor_names` 为键的 numpy 数组字典；`return_type` 控制批量格式，`return_meta_info=True` 返回 `(result, meta_info)`。
- 区分在线 `return_dict=True` 的 schema key 与批量训练列名：如 MACD 的在线 key 是 `dif/dea/macd`，批量列名是 `MACD(26,12,9)[close].dif` 等。单输出的 `factor_names` 是 `[full_name]`。
- pyta2 负责 rolling 指标；sigma2 负责市场输入和 Signal 生命周期。通用 `pyta2_signal()` 可绑定 pyta2 指标；已有稳定因子优先使用具名 `rKlineX` / `KlineX`。
- future target 的输出对应较早的 anchor，不是当前时点可用特征；`sigma2.kline.target` 的现有类不支持 `update_last()`。解释结果时给出当前索引和 anchor 索引。

## 新增 Signal

按 [新增信号指南](references/add-signals.md) 判断因果时点、family、状态、身份、导出和验证范围。用户要求重新设计公共接口时，按仓库 `AGENTS.md` 先使用 `api-design-zh`；沿用现有接口时直接按当前契约实现。
