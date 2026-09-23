# PLAN-020：删除兼容层

更新时间：2026-09-23 10:34 CST

状态：已完成

设计依据：`docs/design/compatibility-removal-20260923-overview.md`

## 目标

按用户“不考虑兼容性”的要求，让 0.4.0 源码只保留当前公共 API 和当前生命周期契约，删除明确为旧版本或本地仓库布局保留的兼容代码。

## 实施步骤

1. 版本提升至 `0.4.0`，声明 `pyta2>=0.0.1` 安装依赖。
2. 删除 `kline/compat/`、旧根转发模块、`effect/`、`kline/pyta2/`、`_factor.py`，清理顶层及 K 线包旧名称属性。
3. 删除仅服务旧 `rSMA` 的 component schema override。
4. 删除 pyta2 相邻仓库导入兜底、旧子类自动快照兜底和适配器旧 `forward()` 分支。
5. 整理现有测试中的兼容专用内容，保留 canonical API 的既有检查；更新 README、当前设计入口及因子模板。
6. 静态审阅导入引用、代码差异和格式；修复发现的问题，生成 OUTCOME，追加 INDEX，提交并立即推送。

## 完成标准

- 旧名称、旧模块和旧路径不再由包导出或存在于源码。
- K 线 canonical 入口、target 和通用 pyta2 bridge 仍有单一明确落点。
- 内部不再修改 `sys.path` 寻找 pyta2，安装依赖由包元数据声明。
- 状态快照只恢复显式字段；不再整份复制旧子类状态。
- 当前文档与源码一致，历史计划和结果保持当时记录。
- 提交只包含本计划相关跟踪文件，不包含现有用户工作区改动。

## 执行约束

用户未要求运行测试；本计划使用代码 review、静态引用检索、lint 与语法检查确认改动。测试文件只清除因旧兼容接口删除而失效的部分，不新增测试。

## 执行摘要

- 已删除旧 K 线短名称、compat/、旧根模块、effect/、pyta2/sma 及 `_factor.py` 转发层；当前分类包和 target 保留单一实现。
- 已移除旧子类自动快照、pyta2 相邻仓库导入兜底、适配器直接 `forward()` 的旧分支，以及兼容专用的 component schema override。
- 已提升版本至 `0.4.0` 并声明 pyta2 依赖，整理 README、设计和现有测试文件。
- 代码 review 修复了一处无用导入；Ruff、compileall、引用检索与 diff whitespace 检查通过。按执行约束未运行测试。
