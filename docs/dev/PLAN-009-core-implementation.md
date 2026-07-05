# PLAN-009 core implementation

更新时间：2026-07-05 14:32 CST

## 背景

当前仓库已经完成 sigma2 核心设计收敛，但尚未实现 Python 包代码。根据 `docs/design/sigma2-20260704-overview.md`，第一阶段应先实现类似 `pyta2.base.rIndicator` 的轻量继承式 rolling signal 核心，而不是先实现 `FeatureSet`、minbt adapter 或复杂 DAG。

## 目标

实施最小稳定核心，使用户可以直接继承 sigma2 类定义和运行信号：

- 创建可安装的 Python 包骨架。
- 实现 `rSignal`，对齐 `rIndicator` 的状态、schema、输出缓存和元信息心智。
- 将公共状态推进入口固定为 `step()`。
- 保持 `forward()` 为子类计算 hook，直接调用不推进生命周期。
- 实现 `rKlineSignal`、`rKlineWindowSignal`、`rOrderBookSignal`、`rTradeSignal`。
- `rKlineWindowSignal` 内部使用 `pyta2.utils.deque.DequeTable` 维护 OHLCV 窗口。
- 实现最小 `rPyta2Signal` 和 pyta2 name resolver，支持 `rPyta2SMA` 这类类式快捷定义。
- 实现几个可运行示例信号，覆盖单点 K 线、窗口 K 线、orderbook、trade。
- 编写 contract tests 锁住核心生命周期、输出契约、reset、窗口语义和 experimental family 基本输入契约。

## 非目标

- 不实现 `FeatureSet`。
- 不实现 DataFrame batch / ML matrix builder。
- 不实现 minbt adapter。
- 不实现完整 pyta2 全指标 catalog；本轮只做最小 name resolver 和 `rPyta2SMA` 类式快捷入口。
- 不引入新的公共 ring buffer / circular buffer 抽象。
- 不为同周期 K 线修正加入 `update()` 或 `step(mode=...)`。

## 实施方案

### 包结构

```text
sigma2/
  __init__.py
  base/
    __init__.py
    signal.py
  families/
    __init__.py
    kline.py
    orderbook.py
    trade.py
  adapters/
    __init__.py
    pyta2.py
  signals/
    __init__.py
    kline.py
    orderbook.py
    trade.py
    shortcuts.py
tests/
  test_core_signal.py
  test_kline_signals.py
  test_market_families.py
```

### 公共接口

第一版稳定公开：

- `sigma2.rSignal`
- `sigma2.rKlineSignal`
- `sigma2.rKlineWindowSignal`
- `sigma2.rOrderBookSignal`
- `sigma2.rTradeSignal`
- `sigma2.rPyta2Signal`
- `sigma2.rPyta2SMA`
- `sigma2.pyta2_signal`
- `sigma2.resolve_pyta2_indicator`
- `sigma2.rReturn`
- `sigma2.rGap`
- `sigma2.rSMA`
- `sigma2.rBookSpread`
- `sigma2.rTradeSignedVolume`
- `sigma2.Schema`
- `sigma2.Space`
- `sigma2.Scalar`
- `sigma2.Box`

### 关键契约

- `rSignal.step()` 是唯一会推进 `g_index`、调用 `_step_forward()`、缓存输出、处理 `return_dict` 的公共入口。
- `rSignal.forward()` 不推进 `g_index`，不写 `outputs`。
- `rSignal.outputs` 使用 `DequeTable`，与 pyta2 `rIndicator` 心智一致。
- `buffer_size=None` 表示不限制输出缓存长度。
- `rKlineSignal.step()` 只接受关键字参数 `open/high/low/close/volume`。
- `rKlineWindowSignal` 只在自身内部维护 OHLCV 窗口，不改变 `rKlineSignal` 默认行为。
- `rOrderBookSignal`、`rTradeSignal` 第一版作为 experimental family，只冻结最小 step 输入契约。
- `rPyta2Signal` 是适配层对象，但返回标准 `rKlineWindowSignal`；对外仍只暴露 `step()`。
- `rPyta2SMA` 是用户可直接实例化或继承的类式快捷入口，内部通过 resolver 找到 pyta2 rolling class；未来 pyta2 暴露顶层 `rSMA` 或 registry 时，只替换 resolver，不改变用户代码。

## 验证

- 运行 `pytest`。
- 用测试确认 `forward()` 直接调用不改 `g_index` 和 `outputs`。
- 用测试确认 `rKlineWindowSignal` 内部窗口只保留 `required_window` 长度。
- 用测试确认单输出、多输出、mapping 输出和 schema mismatch 的错误语义。
- 用测试确认 `reset()` 清空输出和扩展状态。

## 风险

- `pyta2` 当前是未跟踪软链接，测试依赖本地相邻 pyta2 包可导入。
- pyta2 的 `Schema` 与 `Space` 仍是外部依赖；第一版不复制这些实现，避免偏离 `rIndicator`。
