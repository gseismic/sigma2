# PLAN-008 pyta2 缓存工具复用修订结果

更新时间：2026-07-05 14:25 CST

## 完成内容

- 核对 pyta2 现有缓存工具：
  - `pyta2.utils.deque.NumpyDeque`
  - `pyta2.utils.deque.DequeTable`
  - `pyta2.utils.vector.VectorTable`
- 更新 `docs/design/sigma2-20260704-overview.md`，移除 `RingBuffer` 伪实现名。
- 将 `rKlineWindowSignal` 的内部 OHLCV 窗口伪代码改为 `DequeTable`。
- 新增“内部缓存工具选择”说明，明确：
  - 单列 rolling 状态优先用 `NumpyDeque`。
  - 多列 rolling 窗口和输出短缓存优先用 `DequeTable`。
  - 应用层 batch / ML 长表可用 `VectorTable`。
- 更新 README，明确 sigma2 不新增公共环形缓存抽象。
- 更新 `docs/HANDOFF.md`，同步当前缓存工具选择和下一步实现建议。
- 更新 `docs/dev/INDEX.md`，追加本轮计划与结果。

## 当前结论

`RingBuffer` 不进入 sigma2 设计。

核心设计只定义窗口语义：

```text
step() -> internal window append -> forward(window arrays)
```

具体内部实现优先复用 pyta2：

```text
NumpyDeque: 单列 rolling 状态
DequeTable: 多列 rolling 窗口、输出短缓存
VectorTable: 应用层长表、batch / ML 数据收集
```

## 设计收益

- 避免凭空引入一套新 buffer 概念。
- 与 pyta2 的 `rIndicator` 输出缓存和既有指标实现保持一致。
- 普通信号作者仍只面对 `forward(...)`，不需要理解底层容器。
- 后续实现可以直接复用 pyta2 已测试过的窗口和列式数据结构。

## 后续建议

实现 `rSignal.outputs` 时优先参考 pyta2 `rIndicator` 当前对 `DequeTable` 的用法。实现 `rKlineWindowSignal` 时优先用固定 schema 的 `DequeTable(maxlen=required_window)`。
