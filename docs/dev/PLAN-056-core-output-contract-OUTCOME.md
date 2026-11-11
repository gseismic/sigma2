# PLAN-056：实施结果

- 完成时间：2026-11-12 01:34 CST
- 计划：`docs/dev/PLAN-056-core-output-contract.md`
- 设计：`docs/design/core-input-schema-20261112-overview.md`、`docs/design/bundle-20261111-overview.md`

## 结果

- `schema`、`output_keys`、`used_fields` 和 `g_index` 公开绑定只读；字段列表在构造时固定为 tuple，原有推进和失败锁定不变。
- 新增私有输出配置辅助，实例确定字段顺序、dtype 和缺失哨兵后，在线缓存与批量重放共享配置。无 schema 的首次输出必须使用字符串键，并固定 object 字段及顺序，包括空字典。
- 保持空输入、已有实例续放、Outcome 历史锚点回填、格式预检查与嵌套对象引用语义；更新 README 和设计实施状态。字段绑定只读不代表 Space 或输出表被深冻结。
- 静态审阅了仓内调用方；工作区链接的 pyta2 和 fintools 中未发现 sigma2 导入，minbt 链接目标不存在，无法检查该项目。

## 验证与审阅

- 按用户要求补充必要测试，覆盖单 K 线扁平调用及批量一致性、通用 Bundle、输入描述、只读属性、空结果与非字符串字段、缓存失败锁定、标量/None/数组、引用共享、批量预检查与中断、Outcome 对齐和续放。
- `PYTHONPATH=.:pyta2 pytest -q tests/test_core_output_current.py tests/test_input_schema_current.py tests/test_bundle_current.py`：15 项通过；本地 pyta2 为 `20e22e6`。
- 从本机 Git 历史提取项目声明的 pyta2 固定提交 `65071a84099c30a4d9476c327232da7c057b2caa` 到临时目录，同一组 15 项测试通过，未修改本地依赖目录。
- `ruff check`、`ruff format --check`、`python -m compileall -q sigma2` 和 `git diff --check` 通过。
- 历史测试套件基线已有 22 项失败、13 个收集错误（另有 5 项通过），原因包括使用已移除的旧 API；按本次要求未全面重写，与新增契约测试分开记录。没有将原有 `pyproject.toml` 修改或未跟踪文件纳入提交。
