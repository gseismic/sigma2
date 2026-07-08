# PLAN-017 K线 ATR bound trigger 契约修复

更新时间: 2026-07-08 19:20 CST

## 背景

代码审查发现 `rKlineATRBoundTrigger` 仍保留 `unit` 泛化分支，并且当 `atr_n > n_forward + 1` 时，在线窗口会把 anchor 错误地放到更早位置，导致 target 延迟输出。

同时，`rKlineEffectSignal` 是内部二层包装基类，只适合固定窗口、无反向状态依赖的 pyta2 effect；当前没有把这个契约显式化。

## 目标

- 将 `rKlineATRBoundTrigger` 收口为真正的 ATR-only K 线 target。
- 移除 `unit` 字段模式和旧 `rKlineBoundTrigger` 导出，避免泛化名字误导。
- 修正 ATR warmup 与 future horizon 叠加窗口：有效窗口应为 `atr_n + n_forward`。
- 计算触发时只把 anchor 到当前点的 `n_forward + 1` 根 K 线传给 `pyta2.effect.rBoundTrigger`。
- 对 `x_unit_ub`、`x_unit_lb`、`n_forward`、`atr_n` 做构造期 `ValueError` 校验。
- 让 `rKlineEffectSignal` 显式要求内部调用方确认 effect 是 fixed-window stateless wrapper。
- 补充测试覆盖 `atr_n > n_forward + 1` 的对齐场景、参数校验和内部 base 契约。

## 验证

- `python -m pytest -q`
- `python -m compileall -q sigma2 tests`
- `git diff --check`
