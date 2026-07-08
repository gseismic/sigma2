# PLAN-015 K线 bound trigger 单位模式修正

更新时间: 2026-07-08 18:38 CST

## 背景

`rKlineBoundTrigger` 之前仍保留了 `unit_field` 作为单位来源参数，这不符合当前设计：

- `pyta2.effect.rBoundTrigger` 需要的是 `units`，不是固定 K 线字段。
- K 线 family 的默认单位应该是内部动态计算的 ATR。
- 用户也需要能显式切换成按收盘价百分比等更直观的单位模式。

## 目标

- 将 `unit_field` 修正为 `unit`。
- 默认 `unit="atr"`，内部动态计算 ATR 作为单位序列。
- 支持 `unit="close"`，用于按收盘价尺度计算边界。
- 保留 `x_unit_ub/x_unit_lb/n_forward` 与 `pyta2` primitive 同名同序。

## 验证

- `python -m pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py`
- `python -m compileall -q sigma2`
- `git diff --check`
