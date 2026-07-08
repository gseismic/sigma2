# PLAN-014 K线 bound trigger 参数对齐结果

更新时间: 2026-07-08 18:38 CST

## 实施内容

- `sigma2.kline.effect.bound_trigger.rKlineBoundTrigger` 的构造参数改为:
  - `x_unit_ub`
  - `x_unit_lb`
  - `n_forward`
  - `unit_field="close"`
- 内部 `effect_args` 继续按 pyta2 primitive 原始顺序透传。
- `full_name` 同步为原始参数命名风格，保留 `unit_field` 以表达 K 线 family 的字段绑定。
- `tests/test_kline_effect_signals.py` 更新为新参数名。

## 验证结果

- `python -m pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py`: 通过，11 passed。
- `python -m compileall -q sigma2`: 通过。
- `git diff --check`: 通过。
