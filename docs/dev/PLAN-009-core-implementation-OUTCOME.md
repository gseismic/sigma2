# PLAN-009 core implementation OUTCOME

更新时间：2026-07-05 14:52 CST

## 执行结果

已完成最小稳定核心实现：

- 新增 `pyproject.toml`，建立可测试的 Python 包骨架。
- 新增 `sigma2.rSignal`，实现 `step()`、`forward()` hook、`reset()`、`reset_extras()`、`outputs`、`latest`、`output_keys`、`required_window`、`make_dict_output()` 和 `meta_info`。
- 新增 `sigma2.rKlineSignal`，固定单根已确定 K 线输入：`open/high/low/close/volume`。
- 新增 `sigma2.rKlineWindowSignal`，通过 `pyta2.utils.deque.DequeTable` opt-in 维护 OHLCV 窗口。
- 新增实验性 `sigma2.rOrderBookSignal` 和 `sigma2.rTradeSignal`，分别固定订单簿快照与逐笔成交的最小 `step()` 输入契约。
- 新增 `sigma2.rPyta2Signal`，把 pyta2 rolling indicator 适配为标准 K 线 `step()` signal。
- 新增 `sigma2.pyta2_signal()`、`resolve_pyta2_indicator()`、`register_pyta2_indicator()`，当前支持 `SMA` 名称映射。
- 新增 `sigma2.rPyta2SMA` 类式快捷适配，返回 pyta2 `rSMA` 适配后的标准 signal。
- 新增第一批示例信号：`rReturn`、`rGap`、`rSMA`、`rBookSpread`、`rTradeSignedVolume`。
- 新增内部 `sigma2._pyta2.ensure_pyta2_importable()`，优先使用已安装 pyta2，在本地开发时兼容仓库根目录下的 `pyta2` 软链接。
- 新增 contract tests，覆盖生命周期、输出契约、reset、buffer、K 线窗口、orderbook/trade family 输入契约。

## 验证

已通过：

```bash
python -c "import sigma2; print(sigma2.rSignal.__name__, sigma2.rReturn().full_name, sigma2.rPyta2SMA(3).full_name)"
pytest -q
python -m compileall -q sigma2 tests
```

测试结果：

```text
26 passed
```

## 保留问题

- `pyta2` 当前在本仓库中仍是未跟踪软链接，不作为 sigma2 源码提交。
- `pyta2` 目前不是本仓库内的标准依赖包，正式安装流程需要后续根据内部包发布方式补齐。
- `SignalEngine`、`FeatureSet`、DataFrame batch、minbt adapter 尚未实现。
- pyta2 adapter 当前只内置 `rPyta2SMA` 类和 `SMA` 名称映射；完整 indicator catalog 尚未实现。
- `rOrderBookSignal` 和 `rTradeSignal` 仍处于 experimental，后续需要更多真实信号和 contract tests 后再冻结。
