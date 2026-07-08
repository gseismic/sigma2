# PLAN-015 K线 bound trigger 单位模式修正结果

更新时间: 2026-07-08 18:38 CST

## 实施内容

- `rKlineBoundTrigger` 新增 `unit` 参数，默认值为 `atr`。
- `unit="atr"` 时，内部维护 `rATR` 状态，动态生成单位序列。
- `unit="close"` 时，以收盘价作为单位序列，适合按收盘价百分比表达边界。
- `unit` 只保留单位模式，不再暴露 `unit_field` 这种字段绑定含义。

## 验证结果

- `python -m pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py`: 通过，12 passed。
- `python -m compileall -q sigma2`: 通过。
- `git diff --check`: 通过。
