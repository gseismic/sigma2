# sigma2 交接文档

更新时间：2026-09-23 04:49 CST

## 项目背景

sigma2 是面向市场事件的有状态 Signal 与机器学习因子库。稳定核心类似 `pyta2.base.rIndicator` 的继承式体系：每个新观测调用 `step()`，最后观测修订调用 `update_last()`，离线 batch 逐条 replay 同一个 Signal。

pyta2 提供 rolling 指标、schema、窗口、full name 和递推状态；sigma2 提供 kline/orderbook/trade family、字段绑定、市场结构派生、组合逻辑、最终因子身份和运行生命周期。pyta2 直接转 Signal 只保留通用 bridge `rPyta2Signal` / `pyta2_signal()`，不能把 sigma2 扩展成 `rPyta2Xxx` 镜像 catalogue。

长期研究训练层仍是 `FeatureData -> TargetData -> ResearchDataset -> AnalysisReport / EnvBuilder`。这些对象消费 Signal，不进入 core。

## 当前仓库状态

- 仓库：`/Users/mac/pai-studio-fin/library/sigma2`
- 分支：`main`
- 包版本：`0.3.0`
- 当前总设计：`docs/design/sigma2-20260922-v5.md`，设计版本 v5.2。
- 当前实施：`docs/dev/PLAN-019-kline-api-layout.md` 及对应 OUTCOME。
- K 线因子模板：`docs/design/kline-factor-20260922-template.md`。
- `pyta2`、`minbt`、`fintools` 是本地未跟踪软链接，只用于参考或验证，不得提交。
- `docs/ref/` 是用户未跟踪资料，`AGENTS.md` 有用户修改；均不得擅自清理、回退或混入提交。

## 已完成的核心生命周期

- `rSignal.step()` 保存观测前检查点并推进 `g_index`。
- `rSignal.update_last()` 从该检查点重算最后观测，不增加 `g_index`，不追加输出行。
- 连续 `update_last()` 幂等；修订后继续 `step()` 与最终序列完整重放一致。
- `_apply_pyta2()` 在 step 时调用子指标 `rolling()`，在修订时调用 `update_last()`。
- 计算或恢复失败后 Signal 进入 faulted 状态，必须 `reset()` 并重放。
- `factor_names`：单输出使用 full name，多输出使用 `full_name.output_key`。
- kline/orderbook/trade family 均提供 keyword-only 同签名 `update_last()`。
- future target 显式 `supports_update_last = False`，避免把历史 anchor 输出误当成当前 bar 输出。
- `forward_signal_apply()` 校验列式输入并 replay 公共 `step()`，支持 dict、tuple、逐行 list、pandas、polars 和 metadata 返回。

## PLAN-019：K 线 API 与目录

### Canonical API

pyta2 和 sigma2 同时使用时，sigma2 的 K 线入口用 family-qualified 名称避免冲突：

| rolling | batch | canonical 文件 |
| --- | --- | --- |
| `rKlineMA` | `KlineMA` | `kline/trend/ma.py` |
| `rKlineMACD` | `KlineMACD` | `kline/trend/macd.py` |
| `rKlineRSI` | `KlineRSI` | `kline/momentum/rsi.py` |
| `rKlineKDJ` | `KlineKDJ` | `kline/momentum/kdj.py` |
| `rKlineATR` | `KlineATR` | `kline/volatility/atr.py` |
| `rKlineBoll` | `KlineBoll` | `kline/volatility/boll.py` |
| `rKlineReturn` | `KlineReturn` | `kline/price/return_.py` |
| `rKlineGap` | `KlineGap` | `kline/price/gap.py` |

Python 名称改变不影响数据身份：`rKlineRSI(14).full_name` 仍为 `RSI(14)[close]`，schema、factor names、window、数值与 update-last 语义保持不变。

### 浅层分类与 target 安全边界

```text
sigma2/kline/
  price/
  trend/
  momentum/
  volatility/
  target/
  _internal/
  compat/
```

放置优先级是：任何依赖未来 K 线的输出一律进入 `target/`；其余 causal Signal 按主要市场含义分类。`target` 与 trend 等并列虽然混合“数据可用时点”和“市场语义”两个轴，但能以较浅路径提供强泄漏边界；不增加低信息量的 `factor/` 层。

future return/change/high-low 与 ATR bound trigger 的真实实现已从 `effect/` 迁到 `target/`。旧 `effect/` 在 0.3.x 仅转发相同类对象。`.gitignore` 的通用 `target/` 规则已收紧为仓库根 `/target/`，否则 Python 的 `kline/target` 会被错误忽略。

### 单一实现与兼容周期

- canonical 算法只存在于新领域目录；旧 `kline/ma.py` 等文件只转发到 `compat/`。
- `_rKlineIndicatorFactor` 的真实位置是 `kline/_internal/indicator_factor.py`；旧 `_factor.py` 只转发。
- v0.2 短名称仍可显式导入，但不在顶层或 `sigma2.kline.__all__` 中。
- 调用 `rMA/MA`、`rRSI/RSI`、`rReturn/rGap` 等旧入口会发出含替代名和删除版本的 `DeprecationWarning`。
- `rSMA` 与 `rPyta2SMA` 的替代入口是 `rKlineMA(..., ma_type="SMA")`；不新增 `rKlineSMA`。
- 旧短名称、旧根模块和 `effect/` 路径计划在 `0.4.0` 删除。
- `rSMA` 在兼容期保留旧 `sma` schema key；canonical MA 使用 pyta2 的 `ma` key。
- `rPyta2Signal` / `pyta2_signal()` 是正式通用 bridge，不属于弃用对象。

## 因子身份与关键边界

```text
EMA(20)[close]
KAMA(10,2,30,stride=2)[volume]
RSI(14)[close]
MACD(26,12,9)[close].dif
Boll(20,2)[close].mid
KDJ(9,3,3)[high,low,close].k
ATR(20,EMA)[high,low,close]
```

- 一个公开因子原则上一个文件；rolling/batch 成对放在该文件。
- batch replay 是正确性基线，暂不为向量化复制公式。
- output schema key 与训练 factor name 分工，不互相替代。
- `update_last()` 只修订最新观测，不支持任意历史位置 rollback。
- 内置有额外递推状态的 Signal 必须显式声明 `_update_state_fields`。
- `rATR(n=1)` 的 family 历史至少保留两根，以正确使用前收盘价；输出 warmup 仍沿用 pyta2。

## 验证状态

当前 contract tests 覆盖：

- 8 种 MA 及 RSI、MACD、Boll、KDJ、ATR 与 pyta2 数值一致。
- 所有 canonical batch、rolling replay 和重复 `update_last()` 一致。
- pyta2 `rRSI/RSI` 与 sigma2 `rKlineRSI/KlineRSI` 可同时直接导入。
- 旧类、旧 batch、旧模块路径的告警、数值和身份兼容。
- canonical 类只定义在领域目录，future-data 类只定义在 `target/`。
- `rKlineReturn/KlineReturn`、`rKlineGap/KlineGap` 配对。
- orderbook“深度失衡 + pyta2 SMA”组合的父子状态修订。
- target 修订拒绝、factor names、空表、列校验和全部返回格式。

验证命令：

```bash
pytest -q                         # 123 passed
ruff check sigma2 tests           # All checks passed
python -m compileall -q sigma2 tests
```

## 后续高价值工作

1. 按 v5 第 10 节分别实现公开的 `mean_of_mean`、`smoothed_depth_imbalance`、`rolling_trade_imbalance`，验证三个 family 的复杂组合开发体验。
2. 为正式发布明确 pyta2 的安装依赖和版本下界，替代当前本地软链接兜底。
3. 在 `0.4.0` 按迁移数据删除 compat、旧根模块与 `effect/` 路径，并同步删除旧入口测试。
4. 有真实性能数据后再评估 batch replay 优化；优化必须保留与 `step()` 的一致性 oracle。
5. 核心稳定后再做多 symbol online runner、FeatureData/TargetData 与研究训练层。

不要先做全面 pyta2 wrapper catalogue、通用表达式 DAG、任意位置回滚、完整 RL 环境或自动训练框架。
