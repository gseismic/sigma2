# 单 K 线基础组件与工具模块组织

- 创建时间：2026-11-11 21:03 CST
- 状态：按本设计实施。
- 范围：单 K 线的基础组件、pyta2 桥接及其导入路径。

## 目标

sigma2 按 `step()` 接收的数据类型组织代码。`core` 负责与输入类型无关的算子生命周期；每种输入类型在自己的包内组织基础组件与工具。此次以单 K 线为范围，整理散落在根目录的基础类、共享输入层和 pyta2 桥接，为其他输入类型提供可参考的结构。

## 使用场景

| 场景 | 面向使用者的入口 | 频次 |
| --- | --- | --- |
| 使用现成 K 线指标 | `sigma2.rKlineMA` 或 `sigma2.kline.rKlineMA` | 高 |
| 自定义当前 K 线信号 | `sigma2.kline.rKlineSignal` | 高 |
| 自定义未来 K 线结果 | `sigma2.kline.rKlineOutcome` | 中 |
| 将 pyta2 指标绑定到 K 线 | `sigma2.kline.pyta2_signal` 或 `rPyta2Signal` | 中 |
| 编写或查阅 K 线基础组件 | `sigma2.kline.base` | 中 |
| 按名称注册或解析 pyta2 指标 | `sigma2.register_pyta2_indicator`、`sigma2.resolve_pyta2_indicator` | 低 |

## 方案比较

| 方案 | 做法 | 优点 | 代价与决定 |
| --- | --- | --- | --- |
| 全部放入 `base/` | 基类、输入层和 pyta2 桥接放在一起 | 文件集中 | 具体桥接算子与基础契约混在一起，不采用。 |
| `base/` 加 `utils.py` | `base/` 存放基类及共享输入层；`utils.py` 存放 K 线 pyta2 桥接 | 与数据类型的组织目标一致，路径浅 | 工具模块也包含一个可实例化的适配器类；目前只有一个桥接，采用。 |
| `base/` 加 `adapters/` 和 `utils.py` | 基类、适配器和其他工具分别组织 | 适配器边界独立 | 目前新增一层目录的收益有限，不采用；将来适配器确有多个时再评估。 |

## 目录与依赖

```text
sigma2/kline/
  base/
    __init__.py    # 公开 rKlineSignal、rKlineOutcome
    _input.py      # 两类算子共用的 K 线 step 输入处理
    signal.py      # rKlineSignal
    outcome.py     # rKlineOutcome
  utils.py         # rPyta2Signal、pyta2_signal
  price/ trend/ momentum/ volatility/ volume/ outcome/
```

| 原位置 | 新位置 |
| --- | --- |
| `sigma2.kline._input` | `sigma2.kline.base._input`，仍为私有实现 |
| `sigma2.kline.signal` | `sigma2.kline.base.signal` |
| `sigma2.kline.outcome_base` | `sigma2.kline.base.outcome` |
| `sigma2.kline.pyta2` | `sigma2.kline.utils` |

`base` 仅依赖 `core`；K 线指标、未来结果及桥接依赖 `base`。`rKlineOutcome` 与 `rKlineSignal` 都经同一 `_KlineStep` 处理 K 线输入，分别继承 core 的 Outcome 和 Signal，不将未来结果建模为当前信号。其他数据类型本次不迁移，不为其创建尚无实现的类。

当前 `sigma2.utils.pyta2` 同时包含通用名称解析、注册表和 K 线字段默认值。本次不拆分或复制注册表，也不调整其注册、字段别名、默认字段及公开导出。`sigma2.kline.utils` 继续使用现有注册表；将其中 K 线专属规则与跨数据类型规则分离属于另一个设计问题。

## 公共接口与行为

- `sigma2`、`sigma2.kline` 中现有的基类、桥接和具体算子名称继续可用；`sigma2.kline.outcome` 继续导出 `rKlineOutcome`。
- 新增 `sigma2.kline.base` 作为基础类的集中入口。用户选择直接导入实现模块时使用上表中的新路径。
- 按用户选择，旧的 `sigma2.kline.signal`、`sigma2.kline.outcome_base`、`sigma2.kline.pyta2` 路径不保留转发。以前以旧模块路径直接导入的代码需要迁移；基于旧路径序列化的类或实例也可能需要迁移。
- 不改变 `step()` / `forward()` 签名、`is_missing` 行为、输入被拒绝与实例锁定的先后关系、输出对齐、缓存、指标注册表或计算结果。
- 保持 `sigma2.kline` 的按需导入。仓内实现从 `sigma2.kline.base` 导入基类，避免经具体 Outcome 包依赖基类或形成反向依赖。

## 三轮检查

1. **职责与输入**：共享输入层仍仅定义一次；Signal 与 Outcome 共享固定 K 线签名，但时间归属继续由各自 core 基类表达。pyta2 桥接属于具体适配器，不放进 `base`。
2. **导入与注册状态**：根包和 K 线包只重新导出同一类对象；桥接继续引用原有唯一注册表；`base` 不反向依赖具体指标、Outcome 包或桥接。
3. **兼容与行为**：常用聚合导出保持不变，旧深层路径明确移除；直接迁移导致类的 `__module__` 改变，旧序列化数据需由使用方处理。方法签名、缺失值处理、算法与生命周期不变。
