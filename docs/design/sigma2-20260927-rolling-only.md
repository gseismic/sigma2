# sigma2 单向逐条运行设计

创建时间：2026-09-27 12:17 CST

状态：当前设计；此前 `docs/design/` 的全部设计原样归档于 `docs/backup/v2/`。

## 背景与范围

pyta2 的 `rIndicator` 已只保留 `rolling()`，不再提供 `update_last()`。sigma2 的公共逐条入口一直是 `step()`；本次保持这个命名，但使每次 `step()` 都表示新增一条已确定观测。影响 `rSignal`、K 线/盘口/成交 family、pyta2 桥接、组合 Signal、target、批量 replay、文档和示例。历史版本设计仅用于追溯。

## 接口方案比较

| 方案 | 优点 | 代价 | 结论 |
| --- | --- | --- | --- |
| A. 保留 `update_last()`，内部 `reset()` 并重放 | 旧调用方少改代码 | 需要保存完整输入历史；成本和状态所有权不明确，也违背仅逐条新增的要求 | 不采用 |
| B. 保留 `update_last()`，调用时抛异常 | 迁移错误更直接 | 仍把不支持的行为暴露为公共能力，类型检查和补全会误导调用方 | 不采用 |
| C. 移除 `update_last()`，继续以 `step()` 推进 | 单条新观测语义清楚，与现有 sigma2 调用保持一致；子指标只调用 `rolling()` | 使用修订功能的调用方要先确定最终观测，或 `reset()` 后重放 | 采用 |
| D. 同时把 `step()` 改名 `rolling()` | 与 pyta2 同名 | 对 sigma2 使用者增加一次无必要的迁移；市场事件的单条输入仍以 `step()` 更清楚 | 不采用 |

## 定稿契约

1. `rSignal.step(*args, **kwargs)` 每次推进 `g_index` 一次并追加一行输出。K 线、盘口、成交子类维持各自 keyword-only 输入签名。`forward()` 是计算 hook；`reset()` 清空索引、输出及子类状态。
2. `rSignal` 及所有 family 不定义 `update_last()`；移除 `supports_update_last`、`checkpoint_fields`、`_update_state_fields`、末根检查点和恢复 hook。`meta_info` 不再报告修订能力。直接调用被删除的方法会得到 Python 的 `AttributeError`。
3. 子类在 `forward()` 中可维护自有递推状态；持有 pyta2 指标时只在新观测中调用其 `rolling()`，在 reset hook 中调用其 `reset()`。窗口型 family 只 append 当前 K 线，再计算窗口。组合子指标和父 Signal 的索引应同步前进。
4. `forward_signal_apply()` 为每次调用创建新的 Signal，并逐行调用 `step()`；逐条结果与 batch 一致。对于来源系统的末条修正，调用方先提供已确定数据；需要重算时创建新实例或 `reset()` 后从输入序列开头重放。
5. `step()` 计算失败后实例仍进入 faulted 状态，直到 `reset()`；失败调用不追加输出，索引保持上次成功位置。子类可能已改变内部状态，因此调用方必须重放已确认数据。
6. future target 继续放在 `sigma2.kline.target`，其输出指向历史 anchor；取消专门的修订能力标志，不改变 target 的延迟输出计算。
7. 移除公开方法属于不兼容变更，sigma2 版本从 0.5.0 升为 0.6.0。迁移说明与使用示例只展示新增观测和完整重放。

## 三轮查漏补缺

1. **用户接口**：保留常用的 `step()`/`KlineX(data)` 路径；删除所有 family 的同名修订方法，避免只删基类而子类残留。`reset()` 是清晰的重放起点。
2. **状态与性能**：移除每步深拷贝与字段检查点，父 Signal 不保存完整输入；有界 OHLCV 窗口及输出缓存保持原有边界。pyta2 子指标仅按单向 `rolling()` 前进。
3. **错误、时点与迁移**：失败状态保持可程序化检查的 `is_faulted`；target 继续说明 anchor 时点；测试覆盖无修订方法、索引/输出行数、组合子指标同步、reset 重放与 batch 一致。旧设计保留原文，不把历史方案混入当前指导。
