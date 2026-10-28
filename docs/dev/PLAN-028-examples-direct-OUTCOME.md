# PLAN-028：examples 目录直接运行实施结果

完成时间：2026-10-28 08:14 CST
计划：[PLAN-028-examples-direct.md](PLAN-028-examples-direct.md)

## 实施结果

- 调整 7 个引用公共示例数据的脚本：直接运行时从同目录导入 `_data`，作为模块运行时使用相对导入。
- 更新所有编号示例的运行提示与 README，说明在 `examples` 目录直接执行脚本；原有模块运行方式继续可用。

## 审查与验证

- 从 `examples` 目录使用 `python3` 逐个运行 9 个编号示例，均成功。用户的 `p3` 是 `python3` 的 shell 别名。
- 从仓库根目录执行 `python3 examples/09_kline_bundle.py`，运行成功。
- 从仓库根目录以 `python3 -m examples.模块名` 逐个运行 9 个示例，均成功。
- `ruff check examples` 和 `git diff --check` 通过。本次仅修改示例运行方式和说明，未运行测试套件。

运行示例仍需要在所用 Python 环境中安装本项目及其依赖；提交与推送状态以 git 记录为准。
