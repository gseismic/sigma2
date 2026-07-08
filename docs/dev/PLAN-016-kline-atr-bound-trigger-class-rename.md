# PLAN-016 K线 ATR bound trigger 类名收口

更新时间: 2026-07-08 19:05 CST

## 背景

`rKlineBoundTrigger` 已经收敛为单一职责：内部动态计算 ATR 作为单位，构造边界触发 target。
继续使用泛化名字会弱化这个语义，也会给后续扩展造成误解。

## 目标

- 将公开类名收敛为 `rKlineATRBoundTrigger`。
- 保留 `rKlineBoundTrigger` 作为兼容别名，避免现有调用立即失效。
- 更新导出与测试，确保新名字成为主入口。

## 验证

- `python -m pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py`
- `python -m compileall -q sigma2`
- `git diff --check`
