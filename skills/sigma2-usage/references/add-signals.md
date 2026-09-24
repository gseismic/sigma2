# 新增 sigma2 Signal

本指南适用于在 sigma2 仓库增加因子或 family Signal。先读根目录 `AGENTS.md` 的计划、代码和文档约定，以及当前 `sigma2/__init__.py` 和目标 family 的实现。公共 API 取舍不清楚时先做设计，不要直接把实现选择写成新契约。最小有状态扩展示例见 [`examples/06_custom_signal.py`](../../../examples/06_custom_signal.py)；不调用 pyta2 指标的 K 线组合模板见 [`rKlineMeanOfMean`](../../../sigma2/kline/trend/mean_of_mean.py)。

## 1. 判断数据时点和 family

先判断输出是否依赖未来数据：

- 只使用当前及过去观测的值可作为 causal feature，按输入类型继承对应 family 基类。
- 需要未来 K 线才能计算的输出属于 target，放在 `sigma2/kline/target/`，不得当作当下可用特征。参考现有 `rKlineFutureReturn` 等实现；target 的输出时点与正向 Signal 不同，不能照搬 `update_last()` 语义。

当前 family 的单条输入契约：

| family | 基类 | 一条观测 |
| --- | --- | --- |
| K 线 | `rKlineSignal` 或需要 OHLCV 历史窗口时的 `rKlineWindowSignal` | `open/high/low/close/volume` |
| 盘口快照 | `rOrderBookSignal` | 已规范排序的完整 `bids` / `asks` 快照 |
| 逐笔成交 | `rTradeSignal` | 一笔 `price` / `volume` / `side` 事件 |

不要把盘口 snapshot、delta 和独立成交事件混成同一个含糊的输入语义。新增一种市场数据 family 是独立的 API 设计工作；先明确一条观测的输入与修订语义，不要仅为容纳一个新因子就改动现有 family 签名。

## 2. 选择实现模式

### 单个 pyta2 rolling 指标绑定 K 线字段

优先复制 `docs/design/kline-factor-20260922-template.md` 中的 K 线模板。canonical 文件按输出的主要市场含义放在 `sigma2/kline/price/`、`trend/`、`momentum/` 或 `volatility/`：

- 一个公开因子一个文件；rolling 类与 batch 函数同文件。
- 继承内部 `_rKlineIndicatorFactor`，复用 pyta2 指标的 schema、窗口、数值和名称，不复制公式或元信息。
- 使用真实输入字段绑定。多输入指标传完整 `fields`，例如 HLC 输入不能伪装成只绑定 `close`。
- `Kline` 只用于 Python API 避免与 pyta2 重名；不要把它加入训练列 `full_name`。

### 自有公式或有状态组合，不调用 pyta2 指标

参考 [`rKlineMeanOfMean`](../../../sigma2/kline/trend/mean_of_mean.py) 及其[设计说明](../../../docs/design/mean-of-mean-20260924-template.md)。直接继承 `rKlineSignal`，把每次观测需要的状态放在子类，并将修订时必须恢复的字段列入 `_update_state_fields`；`reset_extras()` 重新建立这些状态。`forward()` 只处理当前一根观测，预热不足时自行返回 `NaN`。

纯数值输出可以用 `schema={"mean_of_mean": np.float64}` 声明 dtype，不必在因子文件导入 pyta2 的 `Space`。这只消除因子源码对 pyta2 指标和类型的依赖；sigma2 core 当前仍使用 pyta2 的 schema/缓存工具，安装依赖不变。

### 市场结构派生或组合 Signal

从正确的 family 基类继承，自己定义 schema、`full_name` 和真实输入派生。例如盘口深度失衡先由 sigma2 处理 bids/asks，再通过 `_apply_pyta2()` 调用 pyta2 rolling 指标；详见总设计第 10.6 节。

实现时遵守这些边界：

- `forward()` 只实现算法，不手动推进 `g_index`、追加/替换 `outputs`，也不判断 append 或 revise。
- 保持 `step()` 和 `update_last()` 的输入结构一致。对 pyta2 子指标使用 `_apply_pyta2()`，由 core 在新观测和修订时分派到 `rolling()` / `update_last()`。
- 覆盖 `reset_extras()`，清空 Signal 自有状态和子组件。自有可变递推字段列入 `_update_state_fields`，以便最后观测修订能恢复观测前状态；不要把生命周期子组件列入父 Signal 的 checkpoint 字段。
- 修订计算失败后 Signal 进入 faulted 状态；只有 `reset()` 并重放已确认观测才能继续。不要直接改 `g_index` 或输出缓存。
- 明确 `window` / `extra_window`，使 `required_window` 反映输出需要的观测数量；schema 的输出 key、dtype 与实际结果保持一致。

## 3. 提供配对 batch API

有稳定公开价值的 K 线因子提供同名配对接口：

```text
rKlineExample(...)  # 在线逐条 step/update_last
KlineExample(data, ...)  # 对同一 Signal 逐行 replay
```

batch 函数用 `forward_signal_apply(data, rKlineExample, ...)`；不要维护第二套数学实现。列需求由 `step_input_keys` 决定。默认输出是以 `factor_names` 为键的列字典，可沿用 core 支持的 `return_type` 与 `return_meta_info`。

如果新增的只是内部或非 K 线 Signal，不要为了形式统一而编造没有真实用途的 batch 包装。

## 4. 命名、文件和导出

- K 线公开类用 `rKlineExample`，batch 函数用 `KlineExample`。订单簿、成交信号使用对应 family 的明确名称，例如 `rBookSpread`、`rTradeSignedVolume`。
- 不新增与 pyta2 冲突的 `rRSI`、`rMA` 一类短名称或旧式镜像目录。
- 新实现只保留一个 canonical 文件，不新建转发兼容文件。K 线新文件还应导出到所属领域 `__init__.py` 和 `sigma2/kline/__init__.py`；确认属于稳定高频入口后再加到 `sigma2/__init__.py`。其他 family 同样更新其 family 包导出。
- 所有影响结果的参数必须出现在可复现身份中：复用 pyta2 时沿用 component 名称及字段绑定；sigma2 自有参数应明确进入 `full_name`。多输出 `factor_names` 必须逐项对应 `output_keys`。

## 5. 建立契约验证

为新 Signal 补充项目测试，至少覆盖与实现模式相关的契约：

- pyta2 支撑的因子与 pyta2 结果一致；batch 输出与逐条 `step()` replay 一致。
- 修订当前观测后，再继续下一条观测，与直接输入修订后的完整序列一致；检查连续 `update_last()`、`g_index`、输出行数和 `reset()`。
- 检查 `schema`、`output_keys`、`full_name`、`factor_names`、必需列校验和 family 包导出。
- target 应验证数据时点与 `update_last()` 的拒绝行为，避免未来数据被误用为当前特征。

使用 `_update_state_fields` 的组合 Signal，尤其要验证“派生状态 + pyta2 子指标”同时恢复时的 replay 等价性。扩展完成后按仓库 `AGENTS.md` 执行实施计划、review、结果记录和提交约定。
