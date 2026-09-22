# sigma2 交接文档

更新时间：2026-09-22 22:29 CST

## 项目背景

sigma2 是面向市场事件的有状态 Signal 与机器学习因子库。稳定核心是类似 `pyta2.base.rIndicator` 的继承式体系：每个新观测调用 `step()`，最后观测修订调用 `update_last()`，离线 batch 逐条 replay 同一个 Signal。

pyta2 提供 rolling 指标、schema、窗口、full name 和递推状态；sigma2 提供 kline/orderbook/trade family、字段绑定、市场结构派生、组合逻辑、最终因子身份和运行生命周期。pyta2 直接转 Signal 只保留一个通用薄 bridge，不能把 sigma2 扩展成 `rPyta2Xxx` 镜像 catalogue。

长期研究训练层仍是 `FeatureData -> TargetData -> ResearchDataset -> AnalysisReport / EnvBuilder`。这些对象消费 Signal，不进入 core。

## 当前仓库状态

- 仓库：`/Users/mac/pai-studio-fin/library/sigma2`
- 分支：`main`
- 包版本：`0.2.0`
- 当前总设计：`docs/design/sigma2-20260922-v5.md`，设计版本 v5.1。
- 本轮计划：`docs/dev/PLAN-018-kline-factor-library.md`。
- K 线因子模板：`docs/design/kline-factor-20260922-template.md`。
- `pyta2`、`minbt`、`fintools` 是本地未跟踪软链接，只用于参考或验证，不得提交。
- `docs/ref/` 是用户未跟踪资料，`AGENTS.md` 有用户修改；均不得擅自清理、回退或混入提交。

## PLAN-018 已完成能力

### Core 生命周期

- `rSignal.step()` 保存观测前检查点并推进 `g_index`。
- `rSignal.update_last()` 从该检查点重算最后观测，不增加 `g_index`，不追加输出行。
- 连续 `update_last()` 幂等；修订后继续 `step()` 与最终序列完整重放一致。
- `_apply_pyta2()` 在 step 时调用子指标 `rolling()`，在修订时调用 `update_last()`。
- 计算或恢复失败后 Signal 进入 faulted 状态，必须 `reset()` 并重放。
- `factor_names`：单输出使用 full name，多输出使用 `full_name.output_key`。
- kline/orderbook/trade family 均提供 keyword-only 同签名 `update_last()`。
- future effect/target 明确 `supports_update_last = False`，避免把历史 anchor 输出误当成当前 bar 输出。

### Batch

- `sigma2.core.forward_signal_apply()` 接收列式对象，按 `step_input_keys` 校验列并逐条调用 Signal 公共 `step()`。
- 默认返回以 factor name 为 key 的 `dict[str, np.ndarray]`。
- 支持 tuple、逐行 list、pandas DataFrame、polars DataFrame 与 metadata 返回。
- 支持合法空表；额外输入列被忽略。
- batch 不直接调用 pyta2 batch 公式，因此 finalized batch 与在线 replay 同源。

### 第一批 K 线因子

每个 rolling 类和 batch 函数位于同一个独立文件：

| 文件 | rolling | batch | 输入绑定 |
| --- | --- | --- | --- |
| `sigma2/kline/ma.py` | `rMA` | `MA` | 任意标准 K 线字段 |
| `sigma2/kline/rsi.py` | `rRSI` | `RSI` | 任意标准 K 线字段 |
| `sigma2/kline/macd.py` | `rMACD` | `MACD` | 任意标准 K 线字段 |
| `sigma2/kline/boll.py` | `rBoll` | `Boll` | 任意标准 K 线字段 |
| `sigma2/kline/kdj.py` | `rKDJ` | `KDJ` | 固定 high/low/close |
| `sigma2/kline/atr.py` | `rATR` | `ATR` | 固定 high/low/close |

`rMA` 通过 `ma_type` 支持 SMA、EMA、WMA、HMA、DEMA、TEMA、KAMA、ZLEMA，不新增一组 sigma2 均值子类。`field` 负责 K 线列绑定，`ma_kwargs` 传 KAMA 等高级算法参数；生命周期参数禁止从 `ma_kwargs` 覆盖。

`_rKlineIndicatorFactor` 是六个文件共用的内部 component 接线模板，只复制 pyta2 的 schema/window 元信息并处理字段选择、reset 和生命周期路由。它不是用户 bridge，也不动态生成因子 catalogue。

### 名称示例

```text
EMA(20)[close]
KAMA(10,2,30,stride=2)[volume]
RSI(14)[close]
MACD(26,12,9)[close].dif
MACD(26,12,9)[close].dea
MACD(26,12,9)[close].macd
Boll(20,2)[close].mid
KDJ(9,3,3)[high,low,close].k
ATR(20,EMA)[high,low,close]
```

KAMA 非默认 `stride` 在 pyta2 当前 full name 中缺失，sigma2 会补入最终因子名。ATR 的 ma type 被规范为组件的标准大写名称。`rATR(n=1)` 内部保留两根 HLC 历史，以正确使用前收盘价，但 pyta2 的输出 warmup/window 元信息保持不变。

## 兼容性

- `rSMA`、`rPyta2Signal`、`pyta2_signal()`、`rPyta2SMA` 继续可用。
- 新代码优先使用 `rMA/MA`；不再新增 `rPyta2EMA` 等镜像快捷类。
- 旧 `rSMA` schema key 是 `sma`；新 `rMA(..., ma_type="SMA")` 复用 pyta2 的 `ma`。
- `forward()` 仍是子类计算 hook；runner 只应调用 `step()` / `update_last()`。

## 验证状态

本轮验证覆盖：

- 8 种 MA 与 pyta2 数值一致。
- RSI、MACD、Boll、KDJ、ATR 的 batch、Signal replay、pyta2 三方一致。
- 六类因子的重复 `update_last()` 与最终序列 replay 一致。
- kline/orderbook/trade 的 family 修订签名。
- orderbook“深度失衡 + pyta2 SMA”组合的自身 deque 检查点和子指标修订。
- future target/effect 修订拒绝。
- factor names、空表、列校验和全部返回格式。

验证命令：

```bash
pytest -q                         # 78 passed
ruff check sigma2 tests           # All checks passed
python -m compileall -q sigma2 tests
```

## 重要设计边界

- Signal core 不固定 OHLCV；family 定义单条观测形状。
- 一个公开因子原则上一个文件；rolling/batch 成对放在该文件。
- batch replay 是正确性基线，暂不为了向量化复制公式。
- output schema key 与训练 factor name 分工，不互相替代。
- `update_last()` 只修订最新观测，不支持任意历史位置 rollback。
- future outcome 不是正向因子，不能套用当前 bar 修订语义。
- 内置有额外递推状态的 Signal 必须显式声明 `_update_state_fields`；pyta2/rSignal 子组件由各自生命周期管理，不能放入父级检查点字段。

## 后续高价值工作

1. 按 v5 第 10 节分别实现公开的 `mean_of_mean`、`smoothed_depth_imbalance`、`rolling_trade_imbalance`，验证三个 family 的复杂组合开发体验。
2. 为正式发布明确 pyta2 的安装依赖和版本下界，替代当前本地软链接兜底。
3. 在有真实性能数据后评估 batch replay 优化；优化必须保留与 `step()` 的一致性 oracle。
4. 核心稳定后再做多 symbol online runner、FeatureData/TargetData 与研究训练层。

不要先做全面 pyta2 wrapper catalogue、通用表达式 DAG、任意位置回滚、完整 RL 环境或自动训练框架。
