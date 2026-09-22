# PLAN-018：K 线因子库与 batch 配对接口——执行结果

更新时间：2026-09-22 22:36 CST

状态：完成

对应计划：`docs/dev/PLAN-018-kline-factor-library.md`

设计依据：

- `docs/design/sigma2-20260922-v5.md` v5.1
- `docs/design/kline-factor-20260922-template.md`

## 完成结果

本计划已经把 sigma2 从 v0.1 的 `step()` 单生命周期基线推进到 v0.2.0 的可修订在线因子与同源 batch 因子库。

### 1. Core 生命周期

- `rSignal` 新增 `update_last()`：恢复最近一次普通 `step()` 前的状态，重算并覆盖最后输出。
- 新增声明式 `_update_state_fields`、对象轻量检查点、旧第三方子类 deepcopy 兼容路径。
- 新增 `_apply_pyta2()`，统一子指标的 `rolling()` / `update_last()` 分派。
- 新增 fail-stop：状态计算失败后禁止继续推进，直到 `reset()`。
- 新增 `factor_names`、`supports_update_last`、`is_faulted` metadata。
- kline、orderbook、trade family 暴露与 `step()` 相同的 keyword-only 修订签名。
- K 线窗口修订只替换 OHLCV 最后一行；可用 `history_window` 表达算法所需历史大于输出 warmup 的情况。
- future return/change/high-low/ATR-bound target 明确拒绝 `update_last()`。

### 2. Finalized batch runner

新增 `sigma2/core/batch.py`：

- 接收具有 `keys()` / `__getitem__()` 的列式输入。
- 按 Signal `step_input_keys` 校验必需列、维度和等长约束。
- 只调用对应 Signal 的公共 `step()`，不复制数学公式。
- 默认输出以 `factor_names` 为 key 的 NumPy 列。
- 支持 dict、tuple、逐行 list、pandas DataFrame、polars DataFrame。
- 支持 `return_meta_info=True` 与长度为 0 的合法输入。

### 3. K 线因子配对 API

新增独立文件：

- `sigma2/kline/ma.py`：`rMA/MA`
- `sigma2/kline/rsi.py`：`rRSI/RSI`
- `sigma2/kline/macd.py`：`rMACD/MACD`
- `sigma2/kline/boll.py`：`rBoll/Boll`
- `sigma2/kline/kdj.py`：`rKDJ/KDJ`
- `sigma2/kline/atr.py`：`rATR/ATR`

`rMA` 通过 `ma_type + field + ma_kwargs` 覆盖 pyta2 当前 8 种公开均值算法，避免为算法和字段组合制造大量类。RSI/MACD/Boll 可绑定任意标准 K 线字段；KDJ/ATR 保持 HLC 结构语义。

新增内部 `_rKlineIndicatorFactor`，统一 component schema/window、字段数组选择、reset、生命周期路由和 component metadata；公开因子仍保持一类一文件。

### 4. 因子名称

- 单输出：`full_name` 直接作为 factor name。
- 多输出：`full_name.output_key`。
- 字段 binding 进入名称。
- MA 类型和 component 参数进入名称。
- 补齐 pyta2 KAMA full name 未表达的非默认 `stride`。
- ATR ma type 规范为 component 标准名称，避免大小写造成同值异名。

### 5. 兼容和文档

- 保留 `rSMA`、`rPyta2Signal`、`pyta2_signal()`、`rPyta2SMA`。
- 公共版本提升到 `0.2.0`。
- 更新 README、v5.1 总设计实施状态、交接文档与 K 线因子复制模板。
- 总设计第 10.6 节继续提供 orderbook“多档深度失衡 + pyta2 SMA”完整示例；本轮 contract test 验证了其自身 deque 与子指标共同修订。

## 审阅中发现并修复

1. pyta2 `rATR(n=1)` 的 `required_window` 为 1，但第二根起的 True Range 仍需前收盘价；sigma2 为 ATR 保留至少 2 根 HLC 历史，同时不改变输出 warmup。
2. pyta2 KAMA full name 未包含 `stride`；sigma2 在非默认值时补入，避免机器学习特征列碰撞。
3. ATR 的 `ma_type` 原始大小写会进入 pyta2 full name；现按实际 MA component 名称规范化。
4. 无效 batch `return_type` 原先会在完整 replay 后报错；改为执行前校验。
5. 状态恢复自身失败原先不进入 faulted；现也执行 fail-stop。
6. `history_window` 增加不得小于 `required_window` 的通用约束。
7. `ma_kwargs` 禁止覆盖 buffer、return、extra-window 等生命周期参数。

## 验证结果

```text
pytest -q
78 passed in 1.52s

ruff check sigma2 tests
All checks passed!

python -m compileall -q sigma2 tests
通过
```

数值与状态验证包括：

- SMA/EMA/WMA/HMA/DEMA/TEMA/KAMA/ZLEMA 与 pyta2 batch 一致。
- RSI/MACD/Boll/KDJ/ATR 的 sigma2 batch、逐条 Signal、pyta2 batch 三方一致。
- 六类因子连续多次 `update_last()` 幂等，并与修订后最终序列完整重放一致。
- orderbook 组合 Signal 的 parent deque 检查点和 pyta2 child 修订一致。
- 所有 future target/effect 都拒绝不适用的最后 bar 修订语义。
- factor names、family 导入、空数据、错误列、全部返回格式均有 contract test。

## 未纳入本计划

- FeatureSpec、DAG、任意历史位置 rollback。
- 三个公开复杂组合 Signal 的正式实现。
- 在线多 symbol runner、FeatureData/TargetData、minbt 与训练框架。
- batch 向量化或计算图共享。
- pyta2 的正式发行依赖声明；当前仍使用本地软链接验证。

这些内容保持为后续独立计划，不影响本计划验收。
