# PLAN-011 K 线 effect 包装层

更新时间：2026-07-08 10:13 CST

## 背景

`pyta2.effect` 已提供反向 rolling effect primitive。sigma2 不应把这些 primitive 直接暴露为无数据类型的接口，而应在所属数据 family 中做二层包装。

本计划实现第一批 `kline` 统一输入格式 effect signal:

- 统一 `step(open=..., high=..., low=..., close=..., volume=...)`。
- `forward(opens, highs, lows, closes, volumes)` 接受标准 K 线窗口数组。
- pyta2 继续作为 primitive 层；sigma2 负责 K 线字段绑定和输出语义。

## 设计决策

- 新增 `sigma2/kline/effect/` 子包，作为 K 线 family 下的 effect signals。
- 不把 effect 基类放入 `core/`，避免把 K 线 target 语义污染全局核心。
- 第一批只包装适合在线 `step()` 延迟输出的 stateless future effects。
- 不包装 `rFutureEMA` 等依赖反向调用状态的 effect；这类更适合后续 batch target builder。
- `step()` 输出的是当前 K 线到达后，最早可确定的 anchor target。对于 `horizon=n`，第 `n+1` 次 step 开始返回第一个 anchor 的 target。
- `g_index` 仍表示当前输入流位置；输出 target 的时间对齐由后续 runner / dataset builder 处理。

## 实施范围

新增:

- `sigma2/kline/effect/base.py`
  - `rKlineEffectSignal`
  - 字段绑定、窗口输入、fresh pyta2 effect 调用。
- `sigma2/kline/effect/future_return.py`
  - `rKlineFutureReturn`
- `sigma2/kline/effect/future_change.py`
  - `rKlineFutureChange`
- `sigma2/kline/effect/future_high_low_change.py`
  - `rKlineFutureHighLowChange`
- `sigma2/kline/effect/bound_trigger.py`
  - `rKlineBoundTrigger`

更新:

- `sigma2/kline/effect/__init__.py`
- `sigma2/kline/__init__.py`
- `sigma2/__init__.py`
- `README.md`
- `docs/dev/INDEX.md`

新增测试:

- `tests/test_kline_effect_signals.py`
- 更新 package structure 测试。

## 验证计划

```bash
pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py
pytest -q
python -m compileall -q sigma2 tests
```

## 不做事项

- 不做全量 pyta2.effect catalog 迁移。
- 不做 DataFrame batch target builder。
- 不实现 minbt bridge。
- 不支持 K 线 update/rollback。
