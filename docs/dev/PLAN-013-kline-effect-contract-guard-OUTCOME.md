# PLAN-013 K线 effect wrapper 契约防护结果

更新时间: 2026-07-08 12:50 CST

## 实施内容

- `rKlineEffectSignal.__init__()` 增加固定窗口检查。
- 当 pyta2 effect 的 `window is None` 时立即抛出 `ValueError`，提示 online K 线 wrapper 不支持无界 future effect。
- `tests/test_kline_effect_signals.py` 补充:
  - `rKlineFutureReturn(return_type="log")` 输出 `log_return`。
  - `rKlineEffectSignal` 拒绝 `n_forward=None` 的 pyta2 effect。

## 验证结果

当前 shell 执行环境返回 `137`，本轮尚未完成命令验证。
