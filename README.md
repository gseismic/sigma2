# sigma2

sigma2 是面向金融市场事件的有状态 Signal 与机器学习因子库。当前版本为 `0.4.0`：在线接口按单条事件调用 `step()` / `update_last()`，离线接口按列式数据 replay 同一个 Signal，不维护第二套批量公式。

sigma2 不是 pyta2 的镜像包装器。pyta2 提供 rolling 计算积木、schema、窗口和 full name；sigma2 负责 kline、orderbook、trade 等 family 输入、字段绑定、市场结构派生、组合逻辑、最终因子身份和运行生命周期。pyta2 直接转 Signal 只使用通用桥接器 `rPyta2Signal` / `pyta2_signal()`。

## 当前公共能力

- 核心：`rSignal`、`rKlineSignal`、`rKlineWindowSignal`、`rOrderBookSignal`、`rTradeSignal`。
- 生命周期：`step()` 推进新观测，`update_last()` 修订最后观测，`reset()` 清空状态。
- K 线 rolling/batch 配对：
  - `rKlineMA` / `KlineMA`
  - `rKlineRSI` / `KlineRSI`
  - `rKlineMACD` / `KlineMACD`
  - `rKlineBoll` / `KlineBoll`
  - `rKlineKDJ` / `KlineKDJ`
  - `rKlineATR` / `KlineATR`
  - `rKlineReturn` / `KlineReturn`
  - `rKlineGap` / `KlineGap`
- batch core：`forward_signal_apply()`。
- 训练列身份：`full_name` 与 `factor_names`。
- future target：`rKlineFutureReturn` 等，统一放在 `sigma2.kline.target`，并明确不支持当前 bar 的 `update_last()` 语义。
- orderbook/trade 示例：`rBookSpread`、`rTradeSignedVolume`。

## 与 pyta2 同时使用

公共名称带 `Kline` family，pyta2 primitive 和 sigma2 Signal 可以直接并列导入：

```python
from pyta2 import RSI, rRSI
from sigma2 import KlineRSI, rKlineRSI

primitive = rRSI(14)
signal = rKlineRSI(14, field="close")

primitive_values = RSI(closes, 14)
factor_columns = KlineRSI(kline, 14)
```

`Kline` 只区分 Python API，不进入数据列身份。`rKlineRSI(14).full_name` 仍为 `RSI(14)[close]`，已有训练列无需改名。

## 在线因子

```python
from sigma2 import rKlineMA

ema = rKlineMA(20, ma_type="EMA", field="close")

value = ema.step(
    open=100.0,
    high=103.0,
    low=99.0,
    close=102.0,
    volume=1200.0,
)

# 交易所随后修订同一根 K 线：索引不增加，最后输出被替换。
revised = ema.update_last(
    open=100.0,
    high=104.0,
    low=99.0,
    close=103.0,
    volume=1250.0,
)
```

连续调用 `update_last()` 总是从最近一次普通 `step()` 之前的状态重算，因此不会重复消费当前 bar。计算异常后 Signal 进入 faulted 状态，应 `reset()` 并重放已确认数据。

`rKlineMA` 支持 pyta2 当前公开的 SMA、EMA、WMA、HMA、DEMA、TEMA、KAMA、ZLEMA，可绑定 `open/high/low/close/volume`：

```python
from sigma2 import rKlineMA

volume_kama = rKlineMA(
    10,
    ma_type="KAMA",
    field="volume",
    ma_kwargs={"n2": 2, "n3": 30, "stride": 2},
)

print(volume_kama.full_name)
# KAMA(10,2,30,stride=2)[volume]
```

## 批量因子

batch 函数接收提供 `keys()` 和 `__getitem__()` 的列式对象；普通 dict 和 pandas DataFrame 均可作为输入。K 线 family 的稳定输入列为 `open/high/low/close/volume`，额外列会被忽略。

```python
from sigma2 import KlineMA, KlineMACD

kline = {
    "open": opens,
    "high": highs,
    "low": lows,
    "close": closes,
    "volume": volumes,
}

ma_columns = KlineMA(kline, 20, ma_type="EMA", field="close")
macd_columns = KlineMACD(kline, fast=12, slow=26, signal=9)

print(ma_columns.keys())
# dict_keys(["EMA(20)[close]"])
```

默认返回 `dict[str, np.ndarray]`。`return_type` 还支持：

- `"tuple"`：单输出为数组，多输出为数组 tuple。
- `"list"`：逐行 factor 字典。
- `"dataframe"` / `"pd.dataframe"`：pandas DataFrame。
- `"pl.dataframe"`：polars DataFrame。

传入 `return_meta_info=True` 可获得 `(result, meta_info)`。

## 因子名规则

- 单输出：`factor_names == [full_name]`。
- 多输出：`factor_names == [f"{full_name}.{output_key}", ...]`。

例如：

```text
EMA(20)[close]
RSI(14)[close]
MACD(26,12,9)[close].dif
MACD(26,12,9)[close].dea
MACD(26,12,9)[close].macd
KDJ(9,3,3)[high,low,close].k
ATR(20,EMA)[high,low,close]
```

逐条调用时，`return_dict=True` 仍使用稳定 schema key（如 `dif/dea/macd`）；`factor_names` 负责跨因子的唯一列身份。

## 文件结构与扩展

K 线实现按市场含义使用一层浅分类：

```text
sigma2/kline/
  price/         # Return、Gap
  trend/         # MA、MACD
  momentum/      # RSI、KDJ
  volatility/    # ATR、Boll
  target/        # 依赖未来 K 线的监督目标
  _internal/     # 非公共复用模板
```

放置规则只有两步：任何依赖未来 K 线的输出先进入 `target/`；其余 Signal 按主要市场含义分类。一个 Signal 只有一个 canonical 实现文件，rolling 类与 batch 函数放在同一文件；不按 `simple/composite` 或 `rolling/batch` 再分目录。

由单个 pyta2 component 支撑的新 K 线因子可参考 `docs/design/kline-factor-20260922-template.md`。orderbook 的“多档深度失衡 + pyta2 SMA”组合例见总设计第 10.6 节，它展示了 sigma2 的核心定位：组合结构化市场派生与 rolling component，而不是复刻 pyta2 名称。

### 新增信号

新增 Signal 前先判断输出是否依赖未来数据：依赖未来 K 线的输出属于 `sigma2.kline.target`，不能作为当下可用的 causal feature。其它信号按市场输入选择 K 线、orderbook 或 trade family，并按主要市场含义放入对应目录。

由单个 pyta2 rolling 指标支撑的 K 线因子，沿用 K 线因子模板：一个因子一个 canonical 文件，在线 `rKlineX` 与 batch `KlineX` 同文件，batch 通过 `forward_signal_apply()` replay 同一个 Signal。结构化或组合信号从对应 family 基类实现；自有递推状态需声明 `_update_state_fields`，并通过 `_apply_pyta2()` 驱动 pyta2 子指标的修订生命周期。

新增实现应更新领域包导出，并按公共 API 稳定程度更新 `sigma2.kline` 与顶层 `sigma2` 导出。保持 `full_name` 包含所有影响结果的参数；多输出 `factor_names` 按 schema key 生成。补充 batch/replay、`update_last()`、输出身份和导出契约测试。详细步骤见 [`skills/sigma2-usage/SKILL.md`](skills/sigma2-usage/SKILL.md) 及其[新增信号指南](skills/sigma2-usage/references/add-signals.md)。

## 安装依赖

sigma2 声明 `pyta2>=0.0.1` 为安装依赖。K 线旧短名称与旧模块路径已在 `0.4.0` 删除；当前入口使用 `rKlineX/KlineX` 与 `sigma2.kline.target`。自定义有额外递推状态的 Signal 应通过 `_update_state_fields` 声明修订时需要恢复的字段。

## 设计与验证

- 总设计：`docs/design/sigma2-20260922-v5.md`（v5.3）
- 兼容层清理：`docs/design/compatibility-removal-20260923-overview.md`
- K 线因子模板：`docs/design/kline-factor-20260922-template.md`
- 当前实施计划：`docs/dev/PLAN-020-remove-compatibility.md`

```bash
pytest -q
ruff check sigma2 tests
python -m compileall -q sigma2 tests
```
