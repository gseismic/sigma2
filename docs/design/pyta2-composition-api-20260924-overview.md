# Signal 组合组件与 pyta2 适配接口

创建时间：2026-09-24 16:41 CST
修订时间：2026-09-24 16:50 CST

背景：两级均值 V2 需要两个可修订的 MA 子指标。用户指出 `pyta2` 是独立库，不应在 `rSignal` 基类出现 `_apply_pyta2()`，也不应仅把它改成公开的 `apply_pyta2()`。本设计参考 `pyta2.base.rIndicator` 的检查点、嵌套修订和子指标状态所有权；问题文档仅作为问题线索，最终接口以 sigma2 的边界为准。

## 方案比较

| 方案 | 收益 | 代价 | 结论 |
| --- | --- | --- | --- |
| 保留 `_apply_pyta2()` | 现有实现不用动 | 基类知道外部库，扩展依赖受保护方法 | 淘汰 |
| 将方法公开为 `apply_pyta2()` | 作者不再调用下划线方法 | 外部库名字仍进入通用基类 | 淘汰 |
| 模仿 pyta2 的上下文变量，让任意子对象的 `step()` 自动修订 | 公式处只调用 `step()` | 无法控制 pyta2 私有上下文；对无关 Signal 的嵌套调用也有隐式影响 | 暂不采用 |
| 通用组件协议 + pyta2 适配对象 | 基类只认识 `step/update_last`；外部库转换集中在适配层；公式可组合任意组件 | 创建 pyta2 子指标时需包一层适配对象 | 采用 |

## 定稿接口

`rSignal.apply_component(component, *args, **kwargs)` 在父 Signal 的 `step()` 计算中调用组件的 `step()`，在 `update_last()` 计算中调用组件的 `update_last()`。组件必须提供可调用的这两个方法；父 Signal 不注册、不持有组件，也不替组件重置。此方法只在父 Signal 的这两个生命周期内可调用；生命周期外抛 `RuntimeError`，类型不符合协议时抛 `TypeError`，均不推进组件。组件运行时的异常原样传播，父 Signal 进入 faulted 状态，须 `reset()` 后重放。

`Pyta2Component(indicator)` 位于 `sigma2.utils.pyta2`，仅接受 pyta2 `rIndicator`。它把通用 `step()` 映射到 `indicator.rolling()`，把 `update_last()` 映射到 `indicator.update_last()`，把 `reset()` 映射到 `indicator.reset()`；不改动算法、窗口、schema、索引或 pyta2 自身的检查点。作者持有原指标及适配对象，在 `forward()` 中调用 `self.apply_component(adapter, ...)`，在 reset hook 中重置适配对象。已有单指标桥接及内置 K 线因子也按此路径迁移。

`rSignal.checkpoint_fields: tuple[str, ...] | None` 声明父 Signal 自己需要恢复的字段。`None` 沿用已有 `_update_state_fields`，显式元组覆盖旧声明。`step()` 前保存，`update_last()` 前恢复；连续修订始终从本根观测前恢复。具有 `update_last/reset` 生命周期的子对象不得作为父字段深拷贝，它们自行修订与重置。Signal 自有 deque、标量等可以声明为字段。

迁移时从 `rSignal` 删除 `_apply_pyta2()` 与 `apply_pyta2()`；仓库内调用方全部转到通用接口。旧受保护方法不是稳定公共 API，此次不保留基类别名。既有内置因子直接调用 `forward()` 的测试只要求父索引和父窗口不推进；内置因子可在该历史调用路径直接调用适配器 `step()`，新的公开组合用法仍必须经过父 Signal 的 `step/update_last`。

## 三轮查漏补缺

1. **命名与依赖方向**：基类方法和参数不含 pyta2 概念；pyta2 校验及 `rolling()` 转换只在 `sigma2.utils.pyta2`。core 的 schema 和输出缓存目前仍复用 pyta2 工具，此次只解开组件生命周期耦合，不声称安装时已能去掉 pyta2。
2. **状态所有权与修订**：父 Signal 恢复自有中间队列；每个子组件通过自身 `update_last()` 恢复递推状态。只有内层产生有效观测后才调用外层，两者索引可不同，不能用索引猜测修订模式。`reset()` 要同时清空队列和子组件。
3. **兼容与故障**：V1 完全保留；V2 及既有内置因子转用适配层。直接调用旧受保护方法的第三方代码需迁移为 `Pyta2Component` + `apply_component`。生命周期外公共调用不更改父子状态；生命周期内子组件失败沿用父 Signal 的 fail-stop 规则。
