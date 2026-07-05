# sigma2

sigma2 是面向金融时间序列和机器学习特征工程的信号计算库。它不是 pyta2 的薄封装，也不是以 `FeatureSet` 为中心的应用框架；它的稳定核心是一套类似 `pyta2.base.rIndicator` 的轻量有状态 signal 基类体系。用户应能直接继承 `rSignal` / family 子类定义信号，应用层再把这些信号用于 batch、online、minbt 或 ML 特征矩阵。

## 项目定位

- `sigma2` 的通用核心是 `rSignal`，总体结构应尽量接近 `pyta2.base.rIndicator` 的状态、schema、输出缓存和元信息心智。
- `rSignal.step()` 是唯一公共状态推进入口，调用一次表示输入流推进一个新观测点或事件。
- `rSignal.forward()` 是子类计算 hook，类似神经网络 forward；直接调用不推进 core 生命周期状态、不写输出缓存、不处理 `return_dict`。
- `rSignal` 不提供通用 `rolling()` 或 `update()`；历史窗口和同周期修正不是 core 默认能力。
- `window` 表示产生有效输出所需最少 step 数，不等于 core 必须保存原始输入历史。
- `rKlineSignal` 标准化单根已确定 K 线输入：`open, high, low, close, volume`。
- `rKlineWindowSignal` 为需要 OHLCV 历史序列的 K 线信号 opt-in 维护窗口，内部优先复用 `pyta2.utils.deque.DequeTable`。
- 未来可扩展 `rOrderBookSignal`、`rTradeSignal` 等数据类型专属信号，各自定义标准 `step()` 输入契约。
- `sigma2` 支持自定义信号、组合信号，以及把 pyta2 rolling 指标适配为对外 `step()` 的信号。
- sigma2 不新增公共环形缓存抽象；单列 rolling 状态优先用 `NumpyDeque`，多列 rolling 窗口和输出短缓存优先用 `DequeTable`，应用层长表可用 `VectorTable`。
- `pyta2` 是可复用指标内核和元信息来源，但不是 sigma2 的唯一抽象中心。
- `FeatureSet`、DataFrame batch、online state 和 minbt adapter 属于应用层或适配层，应消费 core，不定义 core。
- 样本裁剪、标签生成、训练集切分和策略回测不属于 sigma2 核心范围。

## 抽象分层

稳定核心：

- `rSignal`：sigma2 通用信号基类，提供 `window`、`schema`、`output_keys`、`required_window`、`step()`、`forward()`、`reset()`、`reset_extras()`、`outputs`、`latest`、`g_index`、`return_dict` 和 `meta_info`。
- `rKlineSignal`：K 线信号基类，固定单根 K 线 `step()` 输入契约。
- `rKlineWindowSignal`：K 线窗口型信号基类，内部用 `DequeTable` 维护 OHLCV 历史序列，给 SMA、ATR、MACD、pyta2 adapter 等使用。
- `rOrderBookSignal`：实验性的订单簿快照 signal family，第一版固定 `step(bids=..., asks=...)`。
- `rTradeSignal`：实验性的逐笔成交 signal family，第一版固定 `step(price=..., volume=..., side=...)`。
- `rPyta2Signal`：把 pyta2 rolling indicator 适配为标准 K 线 `step()` signal。
- `rPyta2SMA`：pyta2 `rSMA` 的类式快捷适配，返回标准 `rPyta2Signal`。

已实现的第一批示例信号：

- `rReturn`
- `rGap`
- `rSMA`
- `rBookSpread`
- `rTradeSignedVolume`

上层能力：

- `pyta2_signal()` / `resolve_pyta2_indicator()`：通过 pyta2 class 或名称构造标准信号，当前已支持 `SMA`。
- `rCompositeSignal`：组合多个 pyta2 指标、sigma2 信号或自定义逻辑，输出新的标准信号。
- `SignalGraph`：组织多个信号之间的依赖、数据类型、拓扑排序和 warmup 传播。
- `SignalEngine`：按数据类型路由输入，并用同一套执行逻辑支持在线 `step()` 和历史 `batch()` replay。
- `FeatureSet`：应用层便利门面，用标准信号对象生成 DataFrame 或 ML 矩阵，不属于 core。
- DSL：后续可提供 `rPyta2ATR`、`rPyta2MACD` 等类式快捷适配，但最终仍是标准信号对象。

## 同周期更新

K 线未完成周期更新、盘口 delta、实盘 preview 等场景真实存在，但不进入 `rSignal` core。它们应由 adapter、stream builder 或 preview runner 处理；正式信号状态只通过 `step()` 追加已确定的新观测点。

## 设计依据

主要依据本地参考文档：

- `pyta2/docs/design/pyta2-sigma-20260627-v3.md`
- `pyta2/pyta2/base/indicator.py`
- `pyta2/pyta2/stats/atr/atr.py`
- `pyta2/pyta2/momentum/macd/macd.py`
- `pyta2/pyta2/trend/ma/sma.py`
- `docs/design/sigma2-20260704-overview.md`

当前仓库中的 `pyta2` 是指向相邻仓库的软链接，只作为设计与验证参考，不应作为 sigma2 源码提交。

当前源码会优先导入已安装的 `pyta2`；如果未安装，会在本地开发环境中尝试识别仓库根目录下的 `pyta2` 软链接。正式环境仍应显式安装或暴露 pyta2。

## 当前状态

本库已经实现最小可验证核心：

- Python 包骨架和 `pyproject.toml`。
- `rSignal.step()` 生命周期、schema 输出、`outputs`、`latest`、`reset()`、`meta_info`。
- `rKlineSignal`、`rKlineWindowSignal`、`rOrderBookSignal`、`rTradeSignal`。
- `rPyta2Signal`、`rPyta2SMA`、`pyta2_signal()`、`resolve_pyta2_indicator()`。
- `rReturn`、`rGap`、`rSMA`、`rBookSpread`、`rTradeSignedVolume`。
- core contract tests。

最小使用示例：

```python
from sigma2 import rPyta2SMA

signal = rPyta2SMA(3, field="close", return_dict=True)

for price in [1.0, 2.0, 3.0]:
    row = signal.step(
        open=price,
        high=price,
        low=price,
        close=price,
        volume=1.0,
    )

print(row)  # {"ma": 2.0}
```

说明：`rPyta2SMA` 当前使用 pyta2 `rSMA`，因此输出 key 沿用 pyta2 schema，为 `ma`。如果需要纯 sigma2 示例信号，可直接使用 `rSMA`。

验证：

```bash
pytest -q
```

后续高优先级工作是扩展 pyta2 indicator catalog、实现最小 `SignalEngine`、应用层 `FeatureSet` / batch replay，以及 minbt adapter。`FeatureSet`、DataFrame batch、minbt adapter 仍应作为应用层继续实现，不能反向定义 core。
