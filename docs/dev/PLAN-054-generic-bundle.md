# PLAN-054：实现通用 Bundle Signal 入口

- 创建时间：2026-11-12 01:21 CST
- 设计：`docs/design/bundle-20261111-overview.md`。
- 状态：已实施并静态审阅。

## 步骤

1. 新增 `sigma2.bundle.base`、`utils.py` 和包级/根级导出，提供 `rBundleSignal.step(bundle, *, time=None)`，直接转发并使用 `bundle` family。
2. 保留 K 线截面的扁平输入与原签名；基类不验证、改写或推断 symbol 对应 value 的结构。
3. 编写使用说明，解释不同算子的输入格式、每步粒度、空截面及输入输出引用责任。
4. 审阅继承链和导出并执行静态检查；运行时测试遵循用户对历史测试限制的确认结果。
5. 记录 OUTCOME 与 INDEX，提交并立即推送本阶段改动。
