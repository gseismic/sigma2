# PLAN-021 执行结果：使用示例与入口文档整理

完成时间：2026-09-24 11:59 CST

对应计划：`docs/dev/PLAN-021-usage-examples-docs.md`

## 结果

- `examples/` 新增六个独立脚本：K 线批量、在线修订、盘口与成交、未来目标、pyta2 桥接、自定义有状态 Signal。`examples/__init__.py` 保证从仓库根目录运行 `python -m examples.<模块名>` 时选中本仓库示例。
- README 现在提供完整输入数据的快速开始、在线修订片段、示例导航、公共入口、训练列名与 schema key 区别，以及未来目标的历史 anchor 语义。
- `skills/sigma2-usage/SKILL.md` 增加明确的触发场景和任务到示例的路由，要求先核对当前源码；新增信号指南补充自定义示例与修订失败后的恢复边界。
- 本次没有修改 `sigma2/` 公共 API 或包依赖。

## 审阅与检查

- 逐个运行六个 `python -m examples.<模块名>`，均正常退出；在线与批量示例的最终值一致，未来收益示例显示索引 2 的输出对应索引 0。
- 执行 README 的三个 Python 代码块，输出与文档注释一致。
- `ruff check examples`、文档相对链接检查及 `git diff --check` 通过。
- 审阅中修复两个实际运行问题：同名第三方 `examples` 包遮蔽示例目录；本地未跟踪的 `pyta2` 软链接遮蔽顶层导出，桥接示例改为传入 `pyta2.momentum.rROC` 类。

本次工作只涉及文档和示例，未新增或运行项目测试套件。`fintools`、`minbt`、`pyta2` 三个本地未跟踪软链接未纳入提交。
