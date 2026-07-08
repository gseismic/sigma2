# PLAN-013 K线 effect wrapper 契约防护

更新时间: 2026-07-08 12:50 CST

## 背景

review `PLAN-012` 后确认两个问题:

- `rKlineEffectSignal` 是 online/window wrapper，不应接受 pyta2 的 `window=None` effect。
- `rKlineFutureReturn(return_type="log")` 是 sigma2 family 层能力，需要测试覆盖。

## 目标

- 在 `rKlineEffectSignal` 构造期拒绝 `effect.window is None`。
- 补充 log return 延迟 target 测试。
- 补充 unbounded pyta2 effect 被拒绝的测试。

## 验证

- `python -m pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py`
- `python -m compileall -q sigma2`
- `git diff --check`
