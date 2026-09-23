# PLAN-019：K 线公共命名与浅层分类迁移

更新时间：2026-09-23 04:49 CST

状态：已完成

设计来源：2026-09-22 至 2026-09-23 关于 pyta2/sigma2 同时使用时的命名冲突，以及 K 线目录扩展方式的接口讨论。

## 目标

1. 让 pyta2 原始指标与 sigma2 K 线 Signal 同时出现时无需依赖临时 import alias 才能理解。
2. 将不断增长的 K 线 Signal 从单一平铺目录迁移到浅层领域目录。
3. 把依赖未来数据的 target 建立为显式安全边界，降低训练特征泄漏风险。
4. 保持 rolling/batch 同文件、同算法、同参数的配对关系。
5. 保持既有 `full_name`、`factor_names` 和数值结果不变。

## 已选方案

### 公共命名

新 canonical API 使用 family-qualified 配对名称：

```text
rKlineMA / KlineMA
rKlineRSI / KlineRSI
rKlineMACD / KlineMACD
rKlineBoll / KlineBoll
rKlineKDJ / KlineKDJ
rKlineATR / KlineATR
rKlineReturn / KlineReturn
rKlineGap / KlineGap
```

这一区分只属于 Python API；训练列身份继续使用 `EMA(20)[close]`、`RSI(14)[close]` 等领域名称，不加入 `Kline`。

### 目录分类

采用固定三层以内的浅层结构：

```text
sigma2/kline/
  price/
  trend/
  momentum/
  volatility/
  target/
  _internal/
  compat/
```

放置规则具有优先级：

1. 任何依赖未来 K 线才能确定的输出，一律进入 `target/`。
2. 其余因果 Signal 按主要市场含义进入 price/trend/momentum/volatility；volume 有实际实现时再建立。
3. 不建立 `batch/`、`rolling/`、`simple/`、`composite/` 或 pyta2 镜像目录。
4. 一个 Signal 只有一个实现文件；复杂组合按输出语义分类，而不是按实现复杂度分类。

### 兼容周期

- 版本提升到 `0.3.0`。
- `rMA/MA`、`rRSI/RSI` 等短名称保留到 `0.4.0`，调用时发出 `DeprecationWarning`。
- `rReturn/rGap/rSMA/rPyta2SMA` 同样进入 compat；`rSMA` 不新增 `rKlineSMA` 对应物，迁移目标是 `rKlineMA(ma_type="SMA")`。
- 原 `sigma2.kline.ma`、`sigma2.kline.effect` 等路径保留薄转发模块一个兼容周期，真实实现只存在于新目录。
- 文档、测试和新代码全部使用 canonical API；兼容测试单独验证旧入口。

## 实施步骤

1. 在 v5 总设计补充 v5.2 命名、目录和兼容决策，并完成三轮边界复核。
2. 创建 `_internal`、price、trend、momentum、volatility、target、compat 包。
3. 迁移真实实现并改为 `rKlineX/KlineX` canonical 名称；为 Return/Gap 补齐 batch 配对。
4. 将原文件改为无算法的兼容转发层，并集中实现弃用提示。
5. 更新 `sigma2.kline`、顶层 `sigma2` 以及各分类包导出。
6. 更新 README、模板、交接和结构 contract tests。
7. 验证新旧入口、pyta2/sigma2 并用、数值、update-last、target 边界和所有历史回归。
8. review 后修复问题，生成 OUTCOME、追加 INDEX，提交并立即推送。

## 验收标准

- canonical 名称可以从分类包、`sigma2.kline` 和顶层 `sigma2` 导入。
- `pyta2.rRSI/RSI` 与 `sigma2.rKlineRSI/KlineRSI` 可在同一模块直接导入且无重名。
- K 线真实实现按约定目录落位；旧路径只含转发代码。
- 任意 future-data Signal 只在 target 真实实现目录中定义。
- rolling 与 batch 仍在同一个实现文件中。
- 旧短名称在调用时给出清晰迁移目标，并保持结果兼容。
- full name、factor names、schema、window、数值和 update-last 行为不变。
- 原测试与新增迁移 contract tests 全部通过，Ruff 和 compileall 通过。
- 提交不包含用户的 `AGENTS.md`、`docs/ref/` 或本地软链接。

## 非目标

- 不新增技术指标公式。
- 不建立动态 registry、自动代码生成或表达式 DAG。
- 不在本计划实现 volume、orderbook 或 trade 的新指标。
- 不删除历史计划文档中当时准确的旧路径记录。

## 执行摘要

- 已新增 family-qualified canonical API，并将真实实现迁入 price、trend、momentum、volatility、target 浅层目录。
- 已把旧短名称集中到 compat，保留原签名和数值契约，调用时报告替代入口与 `0.4.0` 删除版本。
- 已把旧根模块、`effect/` 和 `_factor.py` 收口为无公式转发；`rSMA` 也改为复用 pyta2 组件。
- 已保持 full name、factor names、schema/window、数值与 update-last 行为；Return/Gap 新增 batch 配对。
- 已更新 v5.2 总设计、README、因子模板、交接与迁移 contract tests。
- 已通过 123 项测试、Ruff、compileall、package discovery 和 diff whitespace 检查。
