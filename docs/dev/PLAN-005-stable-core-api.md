# PLAN-005 稳定核心 API 设计

更新时间：2026-07-04 16:31 CST

## 背景

用户进一步明确：`FeatureSet` 这类能力可以在应用层完成，sigma2 的核心应像 `pyta2.base.rIndicator` 一样轻量，用户直接继承一个类即可定义信号。

这要求修正前一版 `FeatureSet` 优先的系统设计，把稳定核心改为 `rSignal` / family 子类体系。

## 目标

- 明确 sigma2 core 的稳定对象是继承式 rolling signal。
- 明确 `rSignal` 概念、命名和生命周期应尽可能与 `pyta2.base.rIndicator` 保持一致。
- 将 `FeatureSet`、DataFrame batch、minbt adapter、ML 矩阵生成下调为应用层。
- 冻结第一批核心接口：`rSignal`、`rKlineSignal`、schema/output、rolling/update 生命周期。
- 保留 orderbook/trade 的扩展框架，但避免过早冻结不成熟字段。
- 更新 README、交接文档、计划索引和旧系统设计状态。

## 范围

- 新增稳定核心设计文档。
- 更新现有文档中的核心定位。
- 不实现 Python 代码。
- 不修改 `AGENTS.md` 或未跟踪软链接。

## 设计检查

按照 `api-design-zh`：

- `rSignal` / `rKlineSignal` 是开发者公共接口，应稳定、契约完整。
- `FeatureSet` 是用户便利接口，但不是 core，应后稳定。
- 内部输入对象、normalizer、runner 不应泄漏到核心继承式信号接口。
- minbt 等外部框架名不得出现在 core。

## 预期产物

- `docs/design/sigma2-20260704-overview.md`
- `docs/dev/PLAN-005-stable-core-api-OUTCOME.md`
- 更新 `docs/dev/INDEX.md`
- 更新 `docs/HANDOFF.md`
- 更新 `README.md`
- 旧系统设计移入 `docs/design/backup/` 后，仅保留历史追溯价值
