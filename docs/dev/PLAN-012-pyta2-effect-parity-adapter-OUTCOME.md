# PLAN-012 pyta2 effect 原始语义适配结果

更新时间: 2026-07-08 12:35 CST

## 实施内容

- `rKlineEffectSignal` 新增可选 `schema` 覆盖和 `output_transform` 钩子。
- `rKlineFutureReturn` 不再向 pyta2 primitive 传递 `return_type`，而是在 sigma2 family 层把 `pct_change` 映射为:
  - `return_type="simple"`: 输出 `return`。
  - `return_type="log"`: 输出 `log_return`。
- `rKlineBoundTrigger` 继续保留用户接口 `upper/lower/horizon`，内部调用 pyta2 的 `x_unit_ub/x_unit_lb/n_forward` 位置参数。
- `rKlineBoundTrigger` 在 sigma2 family 层把 pyta2 primitive 输出映射为 `trigger/unit_change/trigger_index`。

## 设计结论

pyta2 primitive 层稳定继承 `fintools` 原始命名和逻辑；sigma2 K 线 family 层负责标准化用户输入输出字段。这样可以同时满足二次开发继承原始算法和 ML 训练接口清晰两个目标。

## 验证结果

- `python -m pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py`: 通过，9 passed。
- `python -m compileall -q sigma2`: 通过。
- `git diff --check`: 通过。

## 遗留说明

- 当前只适配已有 K 线 effect wrapper，没有新增 orderbook/trades target。
- 工作区已有 `AGENTS.md` 修改和 `fintools/minbt/pyta2` symlink 未跟随本次提交处理。
