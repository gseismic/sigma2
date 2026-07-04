# PLAN-004 执行结果：补充输入类型驱动的 family 扩展设计

完成时间：2026-07-04 15:50 CST

## 完成内容

- 更新 `docs/design/sigma2-20260704-system-design.md`。
- 增加 `InputType -> SignalFamily -> Signal` 作为核心扩展关系。
- 增加 `FamilyRegistry` 设计，要求 `FeatureSet` 和 `OnlineFeatureState` 只依赖 registry，不写死具体 family。
- 明确新增数据类型通过 `InputType + Normalizer + family module + signal implementations` 加入。
- 明确在线核心接口为 `update(input_obj)` 和 `update_family(family, **data)`，`update_kline(...)` 只是便捷包装。
- 修正 minbt 示例，改为 `MinbtFeatureAdapter(self.state).update_bars(dt, bars)`，不在 core 对象暴露 `update_minbt_bars(...)`。
- 更新 `docs/dev/INDEX.md` 和 `docs/HANDOFF.md`。

## 未完成内容

- 未实现 Python 包代码。
- 未修改 minbt 或 pyta2。
- 未提交 `minbt`、`pyta2` 软链接。
- 未处理既有 `AGENTS.md` 修改。

## 结论

sigma2 的二次开发扩展轴应是输入类型。核心类不应随新增数据类型变化；新增 family 应通过 registry 和模块注册接入。
