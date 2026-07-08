# PLAN-017 K线 ATR bound trigger 契约修复结果

更新时间: 2026-07-08 19:24 CST

## 完成内容

- 确认 `rKlineATRBoundTrigger` 的 ATR 对齐问题属实：当 `atr_n > n_forward + 1` 时，旧实现会把 anchor 放到过早位置，导致 target 延迟输出。
- 将 `rKlineATRBoundTrigger` 收口为 ATR-only：
  - 移除 `unit` 参数和 open/high/low/close/volume 单位分支。
  - 移除旧公开别名 `rKlineBoundTrigger` 及其 root/kline/effect 导出。
  - 将 `name` 改为 `kline_atr_bound_trigger`。
- 修正窗口语义：
  - `window = atr_n + n_forward`，同时覆盖 ATR warmup 和未来触发 horizon。
  - 触发判断只使用 anchor 到当前点的 `n_forward + 1` 根 K 线。
  - ATR units 缓存只保留同一触发窗口内的单位序列。
- 增加构造期参数校验：
  - `x_unit_ub > 0`
  - `x_unit_lb > 0`
  - `n_forward >= 1`
  - `atr_n >= 1`
- 将 `rKlineEffectSignal` 标记为内部 adapter 契约：
  - 直接使用 base 时需要内部调用方显式传入 `_trusted_stateless=True`。
  - 具体 wrapper `rKlineFutureReturn` / `rKlineFutureChange` 已显式声明该契约。
- 更新 README 和 package structure tests，当前用户可见入口只保留 `rKlineATRBoundTrigger`。

## 测试

- `python -m pytest -q`
  - 结果：`40 passed`
- `python -m compileall -q sigma2 tests`
  - 结果：通过
- `git diff --check`
  - 结果：通过

## 结论

本次修复后，K 线 ATR bound trigger 的公开名称、参数、窗口语义和输出对齐一致。后续如果需要 close 百分比、固定金额或其它单位，应新增独立类，例如 `rKlineCloseBoundTrigger`，不再复用 ATR 类上的 `unit` 参数。
