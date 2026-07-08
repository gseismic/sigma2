# PLAN-012 pyta2 effect 原始语义适配

更新时间: 2026-07-08 12:35 CST

## 背景

`pyta2.effect` 已调整为对齐 `fintools/spaces/frozen/effect/_effect` 的原始 primitive 语义:

- primitive 参数使用 `n_forward`、`x_unit_ub`、`x_unit_lb`、`x_unit_retrace`。
- primitive 输出 key 使用 `pct_change`、`atr_change`、`trigger_location` 等原始命名。
- `rBoundTrigger` / `rTrailingTrigger` 恢复原始 backward 逻辑。

sigma2 是 family 包装层，不应要求 pyta2 primitive 使用 K 线用户接口字段名。

## 目标

- 保持 sigma2 K 线 wrapper 的用户接口稳定:
  - `rKlineFutureReturn(..., return_dict=True)` 输出 `return`。
  - `rKlineBoundTrigger(..., return_dict=True)` 输出 `unit_change`、`trigger_index`。
- 让 `rKlineEffectSignal` 支持可选输出 schema 覆盖和输出转换。
- 移除向 `pyta2.effect.rFutureReturn` 传递 `return_type` 的 primitive 参数。
- 测试确认 sigma2 wrapper 不受 pyta2 primitive 原始 schema 影响。

## 非目标

- 不改变 sigma2 的 step 输入协议。
- 不新增 orderbook/trades effect wrapper。
- 不修改 pyta2 源码。

## 验证

- `python -m pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py`
- `python -m compileall -q sigma2`
- `git diff --check`
