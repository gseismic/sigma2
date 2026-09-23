# 兼容层清理设计

更新时间：2026-09-23 10:34 CST

状态：当前设计；接续 `sigma2-20260922-v5.md` 的 v5.2 接口迁移

## 目标与使用场景

用户已明确当前不考虑向后兼容。清理目标是让源码、包入口和文档只表达当前 K 线 API，并使状态生命周期与 pyta2 依赖按当前契约运行。

典型场景按频次排列：

1. 从顶层或 `sigma2.kline` 导入 `rKlineX/KlineX`，不再看到旧短名称。
2. 从分类包导入趋势、动量、波动、价格因子，路径只指向真实实现。
3. 从 `sigma2.kline.target` 导入 future-data Signal，不再有 `effect` 镜像入口。
4. 自定义有状态 Signal 显式声明 `_update_state_fields`，`update_last()` 仅恢复声明的状态。
5. 安装 sigma2 时由包依赖安装 pyta2，不通过运行时修改 `sys.path` 查找相邻仓库。
6. 使用现有通用 `rPyta2Signal` / `pyta2_signal()` 桥接 pyta2 指标。

## 方案比较

| 方案 | 优点 | 代价 | 结论 |
| --- | --- | --- | --- |
| A：保留现有兼容期 | 老调用方继续工作 | 与用户当前要求冲突，入口与实现目录持续重复 | 不采用 |
| B：只删 `compat/` 和旧模块 | K 线目录简化 | 本地导入路径、状态快照和旧 `forward()` 分支仍执行兼容逻辑 | 不完整 |
| C：删除明确的兼容层，并保留当前正式接口 | 代码路径和包契约一致；不引入新的 bridge 架构 | 旧调用方须直接迁到当前接口 | 采用 |

## 接口与实现决策

- 版本推进至 `0.4.0`，按 PLAN-019 已公布的删除点移除 `rMA/MA` 等短名称、`rSMA`、`rPyta2SMA`、`sigma2.kline.compat`、旧 K 线根模块、`sigma2.kline.effect`、`sigma2.kline.pyta2` 和 `_factor.py`。
- `rKlineX/KlineX`、`sigma2.kline.target`、`_internal/indicator_factor.py` 是唯一实现与导出路径。公开 K 线 API 在顶层、`sigma2.kline`、分类包三处保持一致。
- `_rKlineIndicatorFactor` 去掉仅供旧 `rSMA` 使用的 schema override；普通组件直接采用 pyta2 schema。target adapter 自身的 schema 映射用于当前 target 输出，继续保留。
- `rSignal._update_state_fields` 默认空 tuple。有额外可变递推状态的子类必须显式列出字段；移除旧子类整份 `__dict__` 拷贝/恢复的兜底，以及相关私有类型与辅助函数。
- `rPyta2Signal.forward()` 直接按当前组件生命周期调用 pyta2；移除为了旧直接调用契约临时创建组件的分支。`step()` / `update_last()` 仍是公共生命周期入口。
- 移除 `ensure_pyta2_importable()`、自动清理 `sys.modules` 与相邻仓库路径探测。`pyproject.toml` 显式要求 `pyta2>=0.0.1`，当前可用的本地 pyta2 版本为 `0.0.1`。
- 通用 `rPyta2Signal` / `pyta2_signal()`、名称解析与显式注册器仍是当前已实现的公共功能。v5 文档里的实例式 bridge 是后续方案，尚未实施；本次不把尚未落地的方案混进兼容清理。
- 删除只为旧入口存在的测试内容；保留现有 canonical 接口与结果检查。README 和因子模板只描述当前 API。历史 PLAN/OUTCOME 不追改。

## 三轮查漏补缺

### 第一轮：公开入口

顶层 `sigma2`、`sigma2.kline`、分类包的当前 API 都有明确落点。旧短名称必须从实际属性中删除，不能只从 `__all__` 隐藏。旧根模块、`compat/`、`effect/`、`pyta2/` 与 `_factor.py` 整体移除，避免路径仍可偶然导入。

### 第二轮：内部状态与依赖

兼容类删除后，`_rKlineIndicatorFactor.schema` override 没有当前调用方，可以一并删除。状态快照仍需为显式字段保留 deepcopy 与对象检查点协议；只删除自动遍历 `__dict__` 的兜底。移除 pyta2 路径探测时同步补上安装依赖，避免源码导入与打包声明不一致。

### 第三轮：范围边界

列式 batch 返回格式、K 线字段绑定、通用 pyta2 名称解析都服务当前场景，不能仅因有多个输入形式就当作兼容代码。future target 的 schema 转换和禁止 `update_last()` 是语义契约，也不删。历史设计章节保留当时的迁移事实，并在当前设计入口标明此文已取代兼容期决策。

## 风险与迁移

该变更是有意的破坏性删除：旧导入会抛出 `ImportError` 或 `ModuleNotFoundError`，旧子类若依赖自动快照则须声明 `_update_state_fields`。迁移目标是当前 `rKlineX/KlineX`、`sigma2.kline.target` 和 `rKlineMA(..., ma_type="SMA")`。`full_name`、schema、数值及 `step()` / `update_last()` 的当前实现不做迁移。
