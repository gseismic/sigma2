# sigma2

sigma2 是面向金融市场事件的有状态 Signal 与机器学习因子库。当前版本为 `0.2.0`：在线接口按单条事件调用 `step()` / `update_last()`，离线接口按列式数据 replay 同一个 Signal，不维护第二套批量公式。

sigma2 不是 pyta2 的镜像包装器：pyta2 提供 rolling 计算积木、schema、窗口和 full name；sigma2 负责 kline、orderbook、trade 等 family 输入、字段绑定、组合逻辑、最终因子身份和运行生命周期。

## 当前公共能力

- 核心：`rSignal`、`rKlineSignal`、`rKlineWindowSignal`、`rOrderBookSignal`、`rTradeSignal`。
- 生命周期：`step()` 推进新观测，`update_last()` 修订最后观测，`reset()` 清空状态。
- 通用 pyta2 薄桥接器：`rPyta2Signal` / `pyta2_signal()`。
- K 线 rolling/batch 配对：
  - `rMA` / `MA`
  - `rRSI` / `RSI`
  - `rMACD` / `MACD`
  - `rBoll` / `Boll`
  - `rKDJ` / `KDJ`
  - `rATR` / `ATR`
- batch core：`forward_signal_apply()`。
- 训练列身份：`full_name` 与 `factor_names`。
- 示例 Signal：`rReturn`、`rGap`、`rSMA`、`rBookSpread`、`rTradeSignedVolume`。
- future target/effect：`rKlineFutureReturn` 等；它们明确不支持当前 bar 的 `update_last()` 语义。

## 在线因子

```python
from sigma2 import rMA

ema = rMA(20, ma_type="EMA", field="close")

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

`rMA` 支持 pyta2 当前公开的 `SMA`、`EMA`、`WMA`、`HMA`、`DEMA`、`TEMA`、`KAMA`、`ZLEMA`，并可绑定 `open/high/low/close/volume`：

```python
from sigma2 import rMA

volume_kama = rMA(
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
from sigma2 import MA, MACD

kline = {
    "open": opens,
    "high": highs,
    "low": lows,
    "close": closes,
    "volume": volumes,
}

ma_columns = MA(kline, 20, ma_type="EMA", field="close")
macd_columns = MACD(kline, fast=12, slow=26, signal=9)

print(ma_columns.keys())
# dict_keys(["EMA(20)[close]"])

print(macd_columns.keys())
# MACD(26,12,9)[close].dif / .dea / .macd
```

默认返回 `dict[str, np.ndarray]`，key 可直接作为机器学习特征列名。`return_type` 还支持：

- `"tuple"`：单输出为数组，多输出为数组 tuple。
- `"list"`：逐行 factor 字典。
- `"dataframe"` / `"pd.dataframe"`：pandas DataFrame，按需依赖 pandas。
- `"pl.dataframe"`：polars DataFrame，按需依赖 polars。

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

逐条调用时，`return_dict=True` 仍使用稳定的 schema key（如 `dif/dea/macd`）；`factor_names` 只负责跨因子的唯一列身份。

## 文件结构与扩展

```text
sigma2/
  core/
    signal.py
    batch.py
    kline.py
    orderbook.py
    trade.py
    pyta2.py
  kline/
    _factor.py
    ma.py
    rsi.py
    macd.py
    boll.py
    kdj.py
    atr.py
    effect/
  orderbook/
    book_spread.py
  trade/
    trade_signed_volume.py
```

每个公开因子独立文件，rolling 类与同名 batch 函数放在一起。由单个 pyta2 component 支撑的新 K 线因子可参考 `docs/design/kline-factor-20260922-template.md`；复杂 Signal 应直接继承 family 基类，并保留市场结构逻辑。

orderbook 的完整组合例见 `docs/design/sigma2-20260922-v5.md` 第 10.6 节：先从 bids/asks 计算多档深度失衡，再交给 pyta2 `rSMA` 平滑。它展示了 sigma2 的核心定位——结构化市场派生与 rolling component 的组合，而不是直接桥接一个 pyta2 名称。

## 兼容入口

现有 `rSMA`、`rPyta2Signal`、`rPyta2SMA` 暂时保留；新代码推荐使用参数化的 `rMA/MA`。`rSMA` 的 schema key 仍为 `sma`，`rMA(..., ma_type="SMA")` 复用 pyta2 schema key `ma`。

本仓库中的 `pyta2` 软链接只用于本地开发与验证，不应提交；正式环境需要安装或暴露 pyta2。

## 设计与验证

- 总设计：`docs/design/sigma2-20260922-v5.md`
- K 线因子模板：`docs/design/kline-factor-20260922-template.md`
- 实施计划：`docs/dev/PLAN-018-kline-factor-library.md`

```bash
pytest -q
ruff check sigma2 tests
python -m compileall -q sigma2 tests
```
