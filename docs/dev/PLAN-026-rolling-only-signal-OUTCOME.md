# PLAN-026 实施结果：Signal 单向逐条运行

更新时间：2026-09-27 12:23 CST

## 完成内容

- 原 `docs/design/` 的 14 个设计文档原文移至 `docs/backup/v2/`，新建 [当前设计](../design/sigma2-20260927-rolling-only.md)。历史计划、结果及旧设计内容未改写。
- `rSignal`、K 线/盘口/成交 family 及内置 Signal 不再定义 `update_last()`；删除检查点、恢复 hook、修订能力标志与元信息。`step()` 每次新增观测，`reset()` 负责从头重放，失败后的 faulted 保护保留。
- pyta2 桥接、单指标 K 线模板及两级均值 V2 只调用子指标 `rolling()`；子指标在父 Signal 重置时同步 `reset()`。窗口型 Signal 仅追加新 K 线。
- README、使用指南与涉及修订的示例改为逐条新增和批量重放；版本升至 `0.6.0`。旧调用方需要先确定输入或重置后完整重放。
- 旧修订测试改为单向索引、输出缓存、父子指标同步、warmup、reset 重放及失败恢复验证。

## 审阅与验证

- 基线：修改前 97 通过、21 失败；失败源于当前 pyta2 已无 `update_last()`。
- 修改后 `pytest -q`：120 通过。
- `ruff check sigma2 tests examples`、`python -m compileall -q sigma2 tests examples`：通过。
- 八个 `examples.01` 至 `examples.08` 的 `main()`：全部运行通过。
- 审阅时修复了盘口组合测试的均值期望，以及两级均值示例流式与批量数据不一致的问题。
- 旧设计逐文件与提交前版本核对内容一致；本地未跟踪软链接 `pyta2`、`fintools`、`minbt` 不纳入提交。

## 边界

当前 pyta2 本地版本号仍为 `0.0.1`，无法用版本下界区分其移除 `update_last()` 前后的发布内容；运行时需安装与本次接口一致的 pyta2。历史计划文档中的旧设计相对路径保留原貌，按本次归档映射到 `docs/backup/v2/` 阅读。
