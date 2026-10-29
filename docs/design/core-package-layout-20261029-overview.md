# sigma2 core 与数据 family 目录设计

创建时间：2026-10-29 14:38 CST  
状态：方案确定，实施见 `docs/dev/PLAN-033-core-package-layout.md`。

## 1. 背景

`sigma2/core` 目前同时保存通用算子生命周期、单 K 线 family、K 线截面 family、订单簿与成交 family、pyta2 K 线适配，以及 K 线字段和截面缓存工具。实际使用入口已经按输入数据类型分成 `sigma2.kline`、`sigma2.kline_bundle`、`sigma2.orderbook`、`sigma2.trade`，但它们仍从 `sigma2.core` 取 family 基类。目录因此没有反映实现的实际归属。

本次整理目标：

1. K 线实现归入 `sigma2/kline`，截面实现归入 `sigma2/kline_bundle`，订单簿和成交 family 分别归入其数据包。
2. 将 `core/signal.py` 中的 `rOperator`、`rSignal`、`rOutcome` 分开为一类一个文件。
3. 让 `core` 只保留跨数据类型的生命周期基类和身份工具；跨 family replay 放在顶层 `sigma2.batch`。
4. 包内实现引用所属 family 的规范路径，不保留旧的 family-specific core 导入兼容层。

## 2. 使用场景与 API 受众

主要受众是使用者和扩展作者：

| 场景 | 预期入口 | 频次 |
| --- | --- | --- |
| 使用内置单 K 线因子 | `sigma2.kline` 或根级 `sigma2` | 高 |
| 编写自定义单 K 线 Signal / Outcome | `sigma2.kline.rKlineSignal` / `rKlineOutcome` | 高 |
| 编写自定义截面算子 | `sigma2.kline_bundle` | 中 |
| 编写订单簿或成交算子 | `sigma2.orderbook` / `sigma2.trade` | 中 |
| 编写不绑定市场 family 的自定义算子 | `sigma2.rSignal` / `sigma2.rOutcome` | 中 |
| 自定义 Signal / Outcome 使用通用生命周期 | `sigma2.core` 或根级 `sigma2` | 中 |

核心概念维持现有名称和运行契约；本设计只调整实现归属和内部模块导入。

## 3. 目录方案比较

| 方案 | 做法 | 优点 | 代价 | 结论 |
| --- | --- | --- | --- | --- |
| A：只移动 K 线基础类 | 仅把 `core/kline.py` 放入 `kline/`，其他文件暂留 `core` | 改动少 | 截面、订单簿、成交及 K 线工具仍与实际 family 分离 | 不采用 |
| B：按 family 归属，core 只留通用生命周期 | family、输入工具和适配器归到数据包；batch 放顶层；移除旧 family-specific core 导入 | 边界清楚，core 足够薄，无重复实现 | 现有 `sigma2.core` family 导入需迁移 | **采用** |
| C：按 family 归属并保留旧 core 转发 | 规范实现归到数据包，core 仅转发旧 family 入口 | 调用方暂时不用迁移 | core 仍暴露 market family，保留额外入口和维护负担 | 不采用 |

采用方案 B。用户明确不要求兼容旧 family 导入。新代码从数据 family 包导入 family 基类；`sigma2.core` 不导出任何 K 线、Bundle、订单簿或成交对象。

## 4. 目标结构和迁移映射

```text
sigma2/
  core/
    operator.py       # rOperator
    signal.py         # rSignal
    outcome.py        # rOutcome
    identity.py       # qualify_factor_name
    __init__.py        # 通用生命周期导出
  batch.py            # 跨 family 的逐条 replay
  kline/
    signal.py
    outcome_base.py
    window.py
    pyta2.py
    _internal/
      data.py
      input.py
      indicator_factor.py
  kline_bundle/
    signal.py
    outcome_base.py
    window.py
    _internal/
      input.py
      symbol_table.py
  orderbook/
    signal.py
  trade/
    signal.py
```

| 当前实现 | 规范位置 |
| --- | --- |
| `core/signal.py:rOperator` | `core/operator.py` |
| `core/signal.py:rSignal` | `core/signal.py` |
| `core/signal.py:rOutcome` | `core/outcome.py` |
| `core/signal.py:qualify_factor_name` | `core/identity.py` |
| `core/kline.py` | `kline/_internal/input.py`、`kline/signal.py`、`kline/outcome_base.py`、`kline/window.py` |
| `core/_kline_data.py` | `kline/_internal/data.py` |
| `core/_indicator_factor.py` | `kline/_internal/indicator_factor.py` |
| `core/pyta2.py` | `kline/pyta2.py` |
| `core/kline_bundle.py` | `kline_bundle/_internal/input.py`、`kline_bundle/signal.py`、`kline_bundle/outcome_base.py`、`kline_bundle/window.py` |
| `core/_symbol_table.py` | `kline_bundle/_internal/symbol_table.py` |
| `core/orderbook.py` | `orderbook/signal.py` |
| `core/trade.py` | `trade/signal.py` |
| `core/batch.py` | `batch.py`，作为跨 family replay API |

旧的 `sigma2.core.kline`、`kline_bundle`、`orderbook`、`trade`、`pyta2` 和私有 helper 模块删除。调用方改用所属 family 包或 `sigma2.batch`。类的 `__module__` 随真实实现位置变化。

## 5. 导入方向

1. 通用 family 基类只依赖 `core.operator`、`core.signal` 或 `core.outcome`。
2. K 线实现只依赖 `kline` 的内部工具和通用 core；Bundle 实现依赖 K 线输入工具及 Bundle 自身工具。
3. orderbook/trade 实现依赖通用 core，不依赖其他 market family。
4. 顶层 `batch.py` 调度各 family 的逐条 replay，不将 market-specific 分支放入 core。
5. `core.__init__` 只导出通用生命周期对象，不导入或转发数据 family。
6. 各数据 family 包公开其基类；根级 `sigma2` re-export 常用 family 和 batch 名称。

## 6. 三轮查漏补缺

### 第一轮：责任归属

- K 线窗口、字段视图、pyta2 indicator adapter 均只服务单 K 线，归入 `kline`。
- 截面输出表和 Bundle 输入视图只服务截面，归入 `kline_bundle`。
- 订单簿与成交 base class 归入对应事件包。
- batch 同时服务多个 family，放在 `sigma2.batch`。

结论：`core` 不持有 market-specific 实现，也不持有跨 family replay。

### 第二轮：导入环与依赖方向

- family 模块引用具体通用 core 子模块，不从 `sigma2.core` 聚合入口导入 family。
- 顶层 `batch.py` 依赖 core 类型和 family 私有输入协议；core 不反向依赖 batch。
- core 聚合只导入通用模块，不提前载入数据 family。
- 不保留兼容模块，避免旧路径继续形成事实 API。

结论：依赖由 family 和 batch 指向通用 core；导入图无反向聚合。

### 第三轮：命名与演进边界

- 通用公共概念由 `sigma2` 和 `sigma2.core` 公开。
- family 基类从所属包公开，私有输入 mixin 和字段工具放入 `_internal`。
- `core/signal.py` 仅定义 `rSignal`；`rOperator`、`rOutcome` 各在独立文件。
- `sigma2.batch` 作为统一 replay API，避免各 family 暴露重复的 batch 调度接口。

结论：此次允许模块路径和 `__module__` 改变；类名、数值、schema、输入输出契约和计算身份保持不变。

## 7. API 迁移范围

- 通用基类从 `sigma2.core` 和根级 `sigma2` 导入。
- K 线 family 从 `sigma2.kline` 导入，Bundle family 从 `sigma2.kline_bundle` 导入；订单簿和成交 family 从对应数据包导入。
- replay API 从 `sigma2.batch` 或根级 `sigma2` 导入。
- `sigma2.core` 不再提供 family、pyta2 adapter、输入 helper、输出表或 batch 导入。
- 算法、运行状态、schema、`full_name`、`factor_names`、输出缓存、预热和 batch 对齐语义不变。

## 8. 验收范围

- 逐个检查 `sigma2/core` 源码归属和所有仓内 core 导入点。
- 核查所有调用方已改用规范 family、batch 和 core 路径。
- 手工审阅新增/移动代码及 diff；本次不运行测试或 lint。
- 记录测试未运行的原因和后续验证范围。
