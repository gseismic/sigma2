# PLAN-011 K 线 effect 包装层结果

更新时间：2026-07-08 10:29 CST

## 完成情况

已完成第一批 K 线 effect signal 包装，实现位置在 `sigma2/kline/effect/`。

## 新增能力

新增 `sigma2/kline/effect/base.py`:

- `rKlineEffectSignal`
- 负责把 stateless `pyta2.effect` 绑定到标准 K 线窗口输入。
- `step()` 仍使用 `open/high/low/close/volume`。
- `forward()` 仍使用 `opens/highs/lows/closes/volumes`。

新增具体 K 线 effect signal:

- `rKlineFutureReturn`
  - 文件: `sigma2/kline/effect/future_return.py`
  - 包装 `pyta2.effect.rFutureReturn`
  - 默认 `field="close"`
- `rKlineFutureChange`
  - 文件: `sigma2/kline/effect/future_change.py`
  - 包装 `pyta2.effect.rFutureChange`
  - 默认 `field="close"`
- `rKlineFutureHighLowChange`
  - 文件: `sigma2/kline/effect/future_high_low_change.py`
  - 输出未来最高价和最低价相对参考字段的路径变动。
  - 默认 `reference_field="close"`。
- `rKlineBoundTrigger`
  - 文件: `sigma2/kline/effect/bound_trigger.py`
  - 包装 `pyta2.effect.rBoundTrigger`
  - 默认 `unit_field="close"`，因此 `upper/lower` 可表示相对 close 的触发距离。

更新导出:

- `sigma2/kline/effect/__init__.py`
- `sigma2/kline/__init__.py`
- `sigma2/__init__.py`

更新说明:

- `README.md`

## 关键语义

- `horizon=n` 的 effect target 需要未来 `n` 根 K 线才能确定。
- 在线 `step()` 返回的是“当前输入到达后最早可确定的 anchor target”。
- `g_index` 仍表示当前输入位置，不表示 target anchor 位置。
- target 对齐、行号偏移、样本裁剪应由后续 runner / dataset builder 处理。
- 当前只包装 stateless future effect。`rFutureEMA` 这类依赖反向调用状态的 effect 不纳入在线 `step()` 包装第一批。

## 测试

新增:

- `tests/test_kline_effect_signals.py`

更新:

- `tests/test_package_structure.py`

已执行:

```bash
pytest -q tests/test_kline_effect_signals.py tests/test_package_structure.py
```

结果:

```text
9 passed
```

已执行:

```bash
pytest -q
python -m compileall -q sigma2 tests
git diff --check
```

结果:

```text
35 passed
```

编译和 diff 检查均通过。

## 未完成事项

- 未做全量 pyta2.effect catalog 迁移。
- 未做 DataFrame batch target builder。
- 未做 minbt bridge。
- 未支持 K 线 update/rollback。
