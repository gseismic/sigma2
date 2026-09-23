# PLAN-019 执行结果：K 线公共命名与浅层分类迁移

完成时间：2026-09-23 04:49 CST

对应计划：`docs/dev/PLAN-019-kline-api-layout.md`

对应设计：`docs/design/sigma2-20260922-v5.md` v5.2

## 结果

PLAN-019 已完成。sigma2 0.3.0 现在使用 `rKlineX/KlineX` 作为 K 线 canonical API，pyta2 primitive 与 sigma2 Signal 可以在同一模块直接导入而不重名。K 线源码从根目录平铺迁为按市场语义组织的浅层目录，future-data 输出由并列的 `target/` 提供显式安全边界。

## Canonical API

新增并从 `sigma2.kline`、顶层 `sigma2` 导出：

```text
rKlineMA / KlineMA
rKlineRSI / KlineRSI
rKlineMACD / KlineMACD
rKlineBoll / KlineBoll
rKlineKDJ / KlineKDJ
rKlineATR / KlineATR
rKlineReturn / KlineReturn
rKlineGap / KlineGap
```

Python API 名称改变不影响数据身份。例如 `rKlineRSI(14).full_name` 仍是 `RSI(14)[close]`；既有 schema、factor names、window、数值和 update-last 行为保持不变。

## 源码落点

真实实现只有一份：

| 目录 | 实现 |
| --- | --- |
| `sigma2/kline/price/` | Return、Gap |
| `sigma2/kline/trend/` | MA、MACD |
| `sigma2/kline/momentum/` | RSI、KDJ |
| `sigma2/kline/volatility/` | ATR、Boll |
| `sigma2/kline/target/` | future return/change/high-low、ATR bound trigger |
| `sigma2/kline/_internal/` | `_rKlineIndicatorFactor` component 接线模板 |
| `sigma2/kline/compat/` | 0.3.x 旧入口兼容对象 |

Return 与 Gap 已补齐 batch 函数。所有 canonical rolling 类与 batch 函数继续同文件，batch 只通过 `forward_signal_apply()` replay 对应 Signal。

原 `sigma2/kline/ma.py` 等根模块、`effect/`、`pyta2/sma.py` 与 `_factor.py` 已变为薄转发文件，不再保存算法。future-data 类的 `__module__` 均指向 `sigma2.kline.target.*`；旧 `effect` 路径返回同一类对象。

## 兼容策略

- 旧 `rMA/MA`、`rRSI/RSI`、`rMACD/MACD`、`rBoll/Boll`、`rKDJ/KDJ`、`rATR/ATR`、`rReturn`、`rGap` 仍可显式导入。
- 旧调用发出 `DeprecationWarning`，消息包含替代名称和 `0.4.0` 删除版本。
- 兼容类与函数保留原公开签名；迁移测试逐项比较 `inspect.signature()`。
- 旧名称不再进入 `sigma2.__all__` 或 `sigma2.kline.__all__`，避免新代码继续由自动补全发现。
- `rSMA` 不新增 `rKlineSMA`；替代入口是 `rKlineMA(..., ma_type="SMA")`。
- `rSMA` 在兼容期保留旧 `sma` schema 和 full name，但计算改为复用 pyta2 SMA component，不保留手写均值公式。
- `rPyta2SMA` 进入兼容期；通用 `rPyta2Signal` / `pyta2_signal()` 仍是正式 bridge。
- 旧短名称、旧根模块和 `effect/` 路径计划在 0.4.0 删除。

## Review 修正

实施后进行了三类复核并修正：

1. **源码身份复核**：确认 canonical 类的 `__module__` 只指向领域目录，旧路径只转发；补齐 target 四个类的模块身份测试。
2. **接口兼容复核**：初版 compat 类使用宽泛 `*args`，会损失 IDE 与反射签名；已改为与 canonical 替代项完全一致的显式签名并增加 contract test。
3. **单一公式复核**：初版兼容 `rSMA` 暂时保留旧手写均值；已为内部 component 模板增加 schema override，使 `rSMA` 在保留旧 schema 的同时复用 pyta2 SMA。
4. **打包复核**：发现 Python 源码目录名 `target/` 会被通用 PyBuilder ignore 规则误伤；已将 `.gitignore` 的 `target/` 收紧为仓库根 `/target/`，并验证 setuptools 能发现 `sigma2.kline.target`。

## 文档

已更新：

- `README.md`：0.3.0 canonical API、并用示例、目录规则和迁移表。
- `docs/design/sigma2-20260922-v5.md`：v5.2 方案比较、三轮设计审阅及实施落点。
- `docs/design/kline-factor-20260922-template.md`：新目录决策、`rKlineX/KlineX` 模板与检查项。
- `docs/HANDOFF.md`：当前代码状态、兼容周期、验证与下一步。

历史 PLAN/OUTCOME 保留当时准确的旧名称和旧路径，没有追改历史事实。

## 验证

```text
pytest -q
123 passed in 5.97s

ruff check sigma2 tests
All checks passed!

python -m compileall -q sigma2 tests
通过

PYTHONPATH=pyta2:. python -W error::DeprecationWarning ...
canonical 并用导入通过；setuptools 发现 15 个 sigma2 包，包含 target 与 compat

git diff --check
通过
```

新增迁移测试覆盖：

- pyta2 `rRSI/RSI` 与 sigma2 `rKlineRSI/KlineRSI` 同时直接导入。
- 旧 rolling、旧 batch 的告警、签名、full name、factor names 和数值兼容。
- `rSMA` 特殊 schema 兼容与 `rPyta2SMA` 数值迁移。
- 旧模块路径转发身份、canonical 实现模块身份和 target 安全边界。
- Return/Gap batch 与 rolling replay 等价。
