# sigma2

sigma2 为金融市场事件提供逐条推进的 Signal 和 Outcome。Signal 的结果属于当前观测；Outcome 等待固定数量的后续观测后，输出属于历史锚点的结果。量化研究和训练系统可以消费这些结果，核心不依赖训练目标的概念。

项目按输入数据分包：`sigma2.kline` 处理单 symbol K 线，`sigma2.kline_bundle` 处理同一时点的多 symbol 截面，`sigma2.orderbook` 和 `sigma2.trade` 分别处理盘口快照和逐笔成交。

## 安装

需要 Python 3.10+。在仓库根目录安装：

```bash
python -m pip install -e .
```

当前 pyta2 的新旧接口都使用 `0.0.1` 版本号，项目依赖固定到 pyta2 提交 `85a2e84969a4a6aa9e201e9f57dc639e4b026827`，安装时需要能够通过 SSH 访问对应仓库。该 pyta2 提交的包初始化会使用 SciPy，因此 sigma2 显式声明 SciPy 依赖。

## 单 symbol K 线

`KlineBar` 表示一根已确定的 K 线，时间必须包含时区。每个算子实例只处理一个 symbol；未指定 symbol 时首次成功输入会绑定它。

```python
from datetime import datetime, timedelta, timezone

from sigma2.kline import KlineBar, KlineMA, rKlineMA

t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
bars = [
    KlineBar("BTC", t0, 100, 101, 99, 100, 10),
    KlineBar("BTC", t0 + timedelta(days=1), 110, 111, 109, 110, 12),
]
signal = rKlineMA(2, return_dict=True)
for bar in bars:
    value = signal.step(bar)
print(value)  # {'ma': 105.0}

columns = KlineMA(bars, 2)
print(columns[signal.factor_names[0]])  # [nan, 105.]
```

批量接口按输入顺序重放同一个 `step()`，默认返回以 `factor_names` 为键的 NumPy 数组字典。`return_type` 还支持 `tuple`、`list`、`dataframe` 和 `pl.dataframe`；`return_meta_info=True` 返回结果和元信息。

## 多 symbol 截面

`KlineBundle` 是同一时间标签的多 symbol 快照。固定的 `symbols` 定义结果顺序；当前时点没有行情的 symbol 不放进 `bars`。数据源负责确认快照何时可以放行。

```python
from datetime import datetime, timedelta, timezone

from sigma2.kline import KlineBar
from sigma2.kline_bundle import KlineBundle, rKlineBundleMA, rKlineBundleRank

t = datetime(2026, 1, 1, tzinfo=timezone.utc)
ready = t + timedelta(days=1)
symbols = ("BTC", "ETH", "SOL")
bundle = KlineBundle(
    bar_time=t,
    symbols=symbols,
    interval="1d",
    time_label="open",
    bars={
        "BTC": KlineBar("BTC", t, 100, 101, 99, 100, 10, ready),
        "ETH": KlineBar("ETH", t, 200, 201, 199, 200, 20, ready),
    },
    available_at=ready,
)
rank = rKlineBundleRank(symbols=symbols, return_dict=True)
ma = rKlineBundleMA(2, symbols=symbols, return_dict=True)
print(rank.step(bundle))  # {'rank': [1., 2., nan]}，输出值为 NumPy 数组
print(ma.step(bundle))    # 第一个快照尚未满足均线预热
```

排名只包含当前字段有效的 symbol，平局使用平均名次。`rKlineBundleReturnRank(n)` 计算过去 N 个共同快照的收益，再在截面上排名。要对其他单 K 线 Signal 计算整个截面，可使用 `rKlineBundleMapSignal`；它为每个 symbol 创建独立状态，缺失 Bar 使用显式占位推进共同时间。

Batch 结果的每个字段形状是 `(时间, symbol)`；`Space` 描述一个 symbol 的值，symbol 顺序由 Bundle 和元信息提供。多维 Space 的结果在 symbol 轴后继续保留其形状。DataFrame 格式按 `(bar_time, symbol)` 展开。

## 未来结果与时间

```python
from datetime import datetime, timedelta, timezone

from sigma2.kline import KlineBar
from sigma2.kline_bundle import KlineBundle, KlineBundleFutureReturn, rKlineBundleFutureReturn

symbols = ("BTC", "ETH")
start = datetime(2026, 1, 1, tzinfo=timezone.utc)
ordered_bundles = []
for i, prices in enumerate([(100, 200), (110, 190), (121, 210)]):
    t = start + timedelta(days=i)
    ready = t + timedelta(days=1)
    bars = {
        symbol: KlineBar(symbol, t, price, price, price, price, 1, ready)
        for symbol, price in zip(symbols, prices)
    }
    ordered_bundles.append(KlineBundle(t, symbols, "1d", "open", bars, ready))

outcome = rKlineBundleFutureReturn(2, symbols=symbols, return_dict=True)
for bundle in ordered_bundles:
    value = outcome.step(bundle)
    if outcome.result_index >= 0:
        print(outcome.result_index, value)

columns, meta = KlineBundleFutureReturn(ordered_bundles, 2, return_meta_info=True)
```

`n_forward=2` 表示等待 2 个输入快照，不自动等同于 2 个自然日。未来收益要求锚点及全部未来区间的对应字段有效，符合当前 pyta2 的缺失规则。在线缓存按结果产生顺序保存；batch 按 `result_index` 回填历史锚点，末尾未成熟位置为缺失值。单 K 线也可使用 `rKlineFutureReturn` 和 `forward_outcome_apply()`。

`bar_time` 是来源声明的 K 线时间标签；`available_at` 是来源确认 Bar 或 Bundle 可用的时间。batch 元信息中的 `result_input_ready_at` 是所有先前输入最早齐备时间，不包含计算和发布延迟。结果的实际可用时间需要由运行或消费层记录；按锚点回填的未来结果不能视为锚点时已知。

## 生命周期与 schema

- `rOperator` 提供共同生命周期，`rSignal` 固定 `n_forward=0`，`rOutcome` 要求 `n_forward>=1`；`result_index = g_index - n_forward`。
- `schema` 直接使用 pyta2 的 `Schema` 与 `Space`。逐条原始返回值、`return_dict`、字段顺序和 `missing_output` 沿用 pyta2 语义；Bundle 的 symbol 轴由 family 添加。
- 输出缓存默认保存最近一步，`buffer_size=0` 或 `None` 关闭，`-1` 无限，正数保存最近 N 步。Bundle 缓存逐 symbol 使用 pyta2 标量表，`outputs[key]` 以时间和 symbol 两个轴查看。
- 修改已处理数据或计算失败后，调用 `reset()` 并从已确认输入序列重放。重置失败时实例保持 faulted；算子状态与输出缓存不是数据源的持久化存储。
- Bundle 的 symbol 顺序、周期和时间标签在一个运行段内固定，时间严格递增。要改变 symbol 集合，建立新运行段；需要连续历史时按新集合重放。

## 从 0.6.0 迁移

- 单 K 线 `step(**ohlcv)` 改为 `step(KlineBar(...))`，批量数据改为 `KlineBar` 序列；横截面使用 `KlineBundle` 序列。
- 未来计算从 `sigma2.kline.target` 迁至 `sigma2.kline.outcome`，`horizon` 改名为 `n_forward`，批量使用 `forward_outcome_apply()`；旧路径不再提供。
- 自定义算子的 schema 改用 pyta2 `Space`，窗口元信息改为 `n_backward`、`n_forward` 和 `min_periods`。输出缓存默认仅保留最近一步，原来依赖无限缓存的调用方需设置 `buffer_size=-1`。

## 示例与扩展

在仓库根目录运行 `python -m examples.09_kline_bundle`。其余例子按 `01` 至 `08` 展示单 K 线、盘口、成交、未来结果、pyta2 组合和自定义 Signal。扩展时参考 [新增信号指南](skills/sigma2-usage/references/add-signals.md)、[核心设计](docs/design/sigma2-operator-signal-outcome-20261028-overview.md) 和 [KlineBundle 设计](docs/design/kline-bundle-20261028-overview.md)。

通用 `pyta2_signal()` 需要显式 `history_window`；调用者应确认具体 pyta2 指标支持该有限窗口。部分 pyta2 指标和 effect 尚未迁移到新基类，不能假定它们均可用于桥接。
