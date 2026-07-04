# PLAN-007 step 核心接口修订结果

更新时间：2026-07-04 17:07 CST

## 完成内容

- 更新 `docs/design/sigma2-20260704-overview.md`，将 sigma2 core 的唯一公共状态推进入口定为 `step()`。
- 明确 `forward()` 是子类实现计算逻辑的 hook，直接调用不推进 core 生命周期状态、不写 `outputs`、不处理 `return_dict`。
- 删除当前设计中 `rolling()` / `update()` 作为 core 稳定接口的定位。
- 明确 `window` 表示产生有效输出所需最少 step 数，不表示 core 默认维护原始输入历史。
- 新增 `rKlineWindowSignal` 设计，用于需要 OHLCV 历史序列的 K 线窗口型信号和 pyta2 adapter；窗口维护发生在 `step()` 调用链的内部 `_step_forward()` 中。
- 明确 `rKlineSignal` 只固定单根已确定 K 线 `step(open, high, low, close, volume)` 输入，不默认维护历史窗口。
- 明确同周期 K 线修正、未完成 K 线 preview、盘口 delta 等不进入 `rSignal` core，应由 adapter、stream builder、preview runner 或独立 delta family 处理。
- 更新 README，改为 `step()` 口径。
- 更新 `docs/HANDOFF.md`，同步当前核心结论和建议下一步。
- 更新 `docs/dev/INDEX.md`，追加本轮计划与结果。

## 当前定稿

核心对象关系：

```text
rSignal.step()
    -> family signal
        -> rKlineSignal
        -> rKlineWindowSignal
        -> rOrderBookSignal experimental
        -> rTradeSignal experimental
    -> concrete signals
    -> adapters/app
```

当前不采用：

```text
rolling() / update() / forward() 作为并列用户入口
```

## 设计收益

- 普通用户、engine、adapter 只有一个正式入库入口：`step()`。
- orderbook/trade 不再被 K 线窗口型输入强制绑定。
- K 线窗口型指标仍然可通过 `rKlineWindowSignal` 复用历史序列。
- pyta2 的 `rolling()` 被限制在 adapter 内部，不污染 sigma2 core。
- 同周期修正不进入 core，避免所有 signal 被迫支持 rollback 或 replace-last 状态语义。

## 后续建议

下一步应直接实现最小 core 与 contract tests：

1. `rSignal.step()` 生命周期。
2. `forward()` 非生命周期语义。
3. `rKlineSignal` 单点输入。
4. `rKlineWindowSignal` opt-in 窗口输入。
5. `rReturn`、`rGap` 示例信号。
6. `rPyta2Signal` 内部 rolling 适配但对外只暴露 step。
