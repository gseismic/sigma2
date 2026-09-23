# PLAN-020 执行结果：删除兼容层

完成时间：2026-09-23 10:34 CST

对应计划：`docs/dev/PLAN-020-remove-compatibility.md`

对应设计：`docs/design/compatibility-removal-20260923-overview.md`

## 结果

sigma2 版本推进到 `0.4.0`。旧 K 线短名称和兼容路径已从源码、顶层 API 与 `sigma2.kline` 导出中移除。保留的入口是 `rKlineX/KlineX`、分类包、`sigma2.kline.target` 以及现有通用 `rPyta2Signal` / `pyta2_signal()`。

具体清理：

- 删除 `sigma2/kline/compat/`、旧 K 线根转发模块、`effect/`、`pyta2/sma.py` 与 `_factor.py`。
- 删除旧 `rSMA` 独用的 component schema override；普通 K 线指标直接采用 pyta2 schema。
- 删除旧子类 `__dict__` 自动快照兜底；`rSignal` 仅恢复 `_update_state_fields` 中显式声明的状态。
- 删除本地软链接与相邻仓库探测、`sys.path` 修改及 pyta2 模块清理逻辑；`pyproject.toml` 声明 `pyta2>=0.0.1`。
- 删除 `rPyta2Signal.forward()` 为直接调用而创建临时组件的旧分支。
- 清理原有兼容测试内容，保留 pyta2/sigma2 并用及 Return/Gap batch 配对检查；更新 README、K 线模板和总设计入口。

## 代码审查

逐项审阅公共导出、模块导入、状态快照和包依赖。静态检索未发现源码或现有测试中仍引用已删除的兼容模块。Ruff 在初次审查中发现 `sigma2/utils/pyta2.py` 的无用 `importlib` 导入，已修复。

## 检查记录

```text
ruff check sigma2 tests              通过
python -m compileall -q sigma2 tests  通过
git diff HEAD --check                 通过
旧兼容标记及旧路径静态检索              无残留引用
```

本任务未要求运行测试，因此没有测试运行结果。已知破坏性边界：旧路径导入会失败；自定义有状态 Signal 必须显式声明 `_update_state_fields`。用户现有的 `AGENTS.md`、`docs/ref/` 和本地软链接未纳入本次改动。
