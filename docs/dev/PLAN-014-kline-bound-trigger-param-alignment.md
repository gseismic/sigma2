# PLAN-014 K线 bound trigger 参数对齐

更新时间: 2026-07-08 18:38 CST

## 背景

`sigma2.kline.effect.rKlineBoundTrigger` 之前使用 `upper/lower/horizon` 作为构造参数。
这与 `pyta2.effect.rBoundTrigger` 的原始接口 `x_unit_ub/x_unit_lb/n_forward` 不一致，
会让用户同时记住两套命名。

## 目标

- 将 `rKlineBoundTrigger` 的构造参数改成 `x_unit_ub/x_unit_lb/n_forward`。
- 保持 `unit_field` 作为 K 线 family 的字段绑定参数。
- 同步更新测试，避免旧参数名残留。

## 验证

- `python -m pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py`
- `python -m compileall -q sigma2`
- `git diff --check`
