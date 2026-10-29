# PLAN-034 结果：精简 core 与单 K 线 MA

- 完成时间：2026-10-29 16:38 CST
- 设计文件：`docs/design/kline-step-core-20261029-overview.md`
- 计划文件：`docs/dev/PLAN-034-kline-step-core.md`

## 实施内容

- core 的 `step` 和 `missing_output` 统一返回 schema 字段字典；移除 `return_dict` 参数，新增只作元信息的 `used_fields`。
- core 可保存未结束观测之前的 `_state`，每次更新从相同快照重算并替换尾行，确认后释放快照。算子需显式声明状态才能使用修订路径；没有声明时提前报错。重置清除快照，推进中出错则锁定实例。
- `rKlineSignal.step` 改为固定 OHLCV 参数，时间和状态参数位于 `*` 之后；整根缺失按 NaN 推进，不做逐条必需字段检查。`step_input_keys` 包含完整签名。
- `rKlineMA` 直接组合 pyta2 均线和所选字段历史；只支持一个周期参数的 SMA、EMA、WMA、HMA、DEMA、TEMA、ZLEMA，输出键固定为 `ma`。`used_fields` 随实例的 `field` 变化。
- MA 导入链不再经过 `_rKlineIndicatorFactor`、`_KlineInput` 和相关字段适配；MA 不再包含 KAMA 特判。根包和趋势包改为按需导出，使 core 和 MA 的导入不顺带加载其他 sigma2 数据 family。
- README 新增 MA 用法及迁移状态说明；其他指标的旧文档保留为后续迁移参考。

## 人工审阅和静态检查

- 按新观测、重复更新、最终确认和重置的顺序审阅状态与索引：每次重算读取原始快照，快照包含 pyta2 指标和输入窗口；缓存关闭后重新启用时，下一次更新写入新缓存。
- 核对 `used_fields` 不参与输入处理，控制参数不作为行情字段；`volume=None` 只在选用 volume 时影响 MA 输入。
- 搜索 core 与根包源码的导入方向，未发现直接导入 sigma2 数据 family；MA 源码只依赖单 K 线 Signal 和 pyta2，不再导入旧 `_internal`。
- 核对项目锁定的 pyta2 提交 `93ab75884e137bc4133b9445bc900a0a8468624c`，其中 `DequeTable` 提供用于替换缓存尾行的 `update_row`。本机未跟踪的 pyta2 链接指向另一提交，相关 MA 源码差异为类型标注调整；未修改该仓库。
- 目标 Python 文件的 Ruff 检查、Ruff 格式检查和 `py_compile` 通过；`git diff --check` 通过。
- 未添加或运行测试，也未运行示例。盘中重算与完整重放的数值一致性、缺失值恢复、各均线类型及深复制性能仍需后续行为验证。

## 未迁移范围和已知影响

- 通用 batch 仍传递已移除的 `return_dict`，尚未适配新的 core；`KlineMA` 批量入口明确抛出 `NotImplementedError`，请使用 `rKlineMA.step`。本轮没有改造通用 batch。
- 其他单 K 线指标仍使用旧的 `required_fields`、窗口和输入约定，可能无法构造或调用；`rKlineBundleMA` 仍使用旧 MA 参数与输入格式，需后续迁移。其他 Bundle、Outcome、订单簿和成交代码也未针对新的 core 接口全面适配。
- 原 `_internal/indicator_factor.py` 的 KAMA 恢复逻辑仍服务未迁移代码，本轮没有修改；新 MA 不支持 KAMA。
- 状态快照要求子类将全部可变计算状态放入 `_state`，并且所含对象支持深复制。省略 `open_time` 时上游须保证当前更新属于同一根；已确认历史被修订时需要重置并重放。
- `pyproject.toml` 版本仍为 0.11.0；当前源码含不兼容接口变化，发布版本时需单独处理版本和剩余迁移。
