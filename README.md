# sigma2

sigma2 是面向金融市场事件的有状态 Signal 与机器学习因子库。当前版本为 `0.3.0`：在线接口按单条事件调用 `step()` / `update_last()`，离线接口按列式数据 replay 同一个 Signal，不维护第二套批量公式。

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
  compat/        # 仅保留到 0.4.0 的旧入口
```

放置规则只有两步：任何依赖未来 K 线的输出先进入 `target/`；其余 Signal 按主要市场含义分类。一个 Signal 只有一个 canonical 实现文件，rolling 类与 batch 函数放在同一文件；不按 `simple/composite` 或 `rolling/batch` 再分目录。

由单个 pyta2 component 支撑的新 K 线因子可参考 `docs/design/kline-factor-20260922-template.md`。orderbook 的“多档深度失衡 + pyta2 SMA”组合例见总设计第 10.6 节，它展示了 sigma2 的核心定位：组合结构化市场派生与 rolling component，而不是复刻 pyta2 名称。

## 0.3.x 兼容入口

0.2.x 的短名称仍可显式导入，但调用时发出 `DeprecationWarning`，并计划在 `0.4.0` 删除：

| 旧入口 | 新入口 |
| --- | --- |
| `rMA/MA` | `rKlineMA/KlineMA` |
| `rRSI/RSI` | `rKlineRSI/KlineRSI` |
| `rMACD/MACD` | `rKlineMACD/KlineMACD` |
| `rBoll/Boll` | `rKlineBoll/KlineBoll` |
| `rKDJ/KDJ` | `rKlineKDJ/KlineKDJ` |
| `rATR/ATR` | `rKlineATR/KlineATR` |
| `rReturn` | `rKlineReturn` |
| `rGap` | `rKlineGap` |
| `rSMA`、`rPyta2SMA` | `rKlineMA(..., ma_type="SMA")` |

旧 `sigma2.kline.ma`、`sigma2.kline.effect` 等模块在 0.3.x 只做转发，不保存第二份算法。`rSMA` 的旧 schema key `sma` 在兼容期保持不变；新 MA 使用 pyta2 schema key `ma`。

本仓库中的 `pyta2` 软链接只用于本地开发与验证，不应提交；正式环境需要安装或暴露 pyta2。

## 设计与验证

- 总设计：`docs/design/sigma2-20260922-v5.md`（v5.2）
- K 线因子模板：`docs/design/kline-factor-20260922-template.md`
- 本次迁移计划：`docs/dev/PLAN-019-kline-api-layout.md`

```bash
pytest -q
ruff check sigma2 tests
python -m compileall -q sigma2 tests
```
