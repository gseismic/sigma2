# PLAN-016 K线 ATR bound trigger 类名收口结果

更新时间: 2026-07-08 19:05 CST

## 实施内容

- 新增公开类 `rKlineATRBoundTrigger`。
- 保留 `rKlineBoundTrigger = rKlineATRBoundTrigger` 作为兼容别名。
- 更新 `sigma2.kline.effect`、`sigma2.kline`、`sigma2` 的导出，确保新名字可直接从顶层导入。
- 更新测试，明确断言新旧名字指向同一个类对象。

## 验证结果

- `python -m pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py`: 通过，12 passed。
- `python -m compileall -q sigma2`: 通过。
- `git diff --check`: 通过。
