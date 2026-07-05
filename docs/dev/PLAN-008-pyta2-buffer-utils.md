# PLAN-008 pyta2 缓存工具复用修订

更新时间：2026-07-05 14:25 CST

## 背景

用户指出：pyta2 已经提供 `pyta2.utils.deque`、`pyta2.utils.vector`、`DequeTable`、`VectorTable`、`NumpyDeque` 等工具，sigma2 设计文档中直接引入 `RingBuffer` 不一定合适。

经核对：

- `pyta2.utils.deque.NumpyDeque` 已提供固定 `maxlen` 的 NumPy-backed rolling deque。
- `pyta2.utils.deque.DequeTable` 是二维列式滚动表，每列由 `NumpyDeque` 管理，适合实时追加和窗口读取。
- `pyta2.utils.vector.VectorTable` 是无 `maxlen` 的列式时间序列表，更适合应用层 batch / ML 长表。
- pyta2 的 `rIndicator` 输出缓存已经使用 `DequeTable`。

## 目标

- 从当前设计文档中移除 `RingBuffer` 具体实现名。
- 明确 sigma2 内部窗口缓存优先复用 pyta2 utils。
- 将 `rKlineWindowSignal` 的默认内部窗口实现建议改为 `DequeTable`。
- 明确 `NumpyDeque`、`DequeTable`、`VectorTable` 的分工。
- 避免把这些内部容器暴露为普通信号开发者必须理解的公共 API。

## 设计判断

- 单列 rolling 状态：优先 `NumpyDeque`。
- 多列 rolling 窗口，例如 OHLCV：优先 `DequeTable`。
- 输出短缓存：沿用 `rIndicator` 心智，优先 `DequeTable`。
- batch / ML 长表：应用层可用 `VectorTable` 或 DataFrame / numpy，不属于 core 状态。
- 不新增公共 `RingBuffer` 概念。

## 修改范围

- `docs/design/sigma2-20260704-overview.md`
- `README.md`
- `docs/HANDOFF.md`
- `docs/dev/INDEX.md`
- 新增本计划结果文件

## 验收标准

- 当前有效设计文档不再把 `RingBuffer` 作为实现名或公共概念。
- 当前有效设计文档明确 `rKlineWindowSignal` 内部窗口建议使用 `DequeTable`。
- 当前有效设计文档说明 `NumpyDeque`、`DequeTable`、`VectorTable` 的适用边界。
- README 和交接文档同步该实现原则。
