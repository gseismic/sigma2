# K 线因子文件模板

更新时间：2026-09-23 04:49 CST

状态：已随 `PLAN-019` 更新，配套 `docs/design/sigma2-20260922-v5.md` v5.2

目标：新增一个由单个 pyta2 rolling 指标支撑的 K 线因子时，保持“按市场语义浅分类、一个因子一个文件、rolling/batch 同文件、计算公式只有一份”。

## 先确定目录

按以下优先级放置：

1. 依赖未来 K 线才能确定输出：一律放入 `sigma2/kline/target/`，不得作为 causal feature。
2. 其余 Signal 按主要市场含义放入 `price/`、`trend/`、`momentum/`、`volatility/`；有真实实现时才新增其它领域包。
3. 不创建 `rolling/`、`batch/`、`simple/`、`composite/` 或新的 pyta2 镜像目录。

复杂程度不是分类轴。例如“均值的均值”仍按输出语义进入 trend 或其它对应领域，不进入 `composite/`。

## 文件模板

假设 Example 属于 trend，复制为 `sigma2/kline/trend/example.py`，再替换类名、函数名和 pyta2 组件：

```python
from pyta2 import rExample as _rPytaExample

from sigma2.core import forward_signal_apply

from .._internal.indicator_factor import _rKlineIndicatorFactor


class rKlineExample(_rKlineIndicatorFactor):
    """Example K 线 Signal。"""

    name = "Example"

    def __init__(
        self,
        n: int = 20,
        *,
        field: str = "close",
        **kwargs,
    ) -> None:
        self.n = n
        super().__init__(
            _rPytaExample(n, buffer_size=0, return_dict=False),
            fields=(field,),
            **kwargs,
        )


def KlineExample(
    data,
    n: int = 20,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
):
    """批量 replay :class:`rKlineExample`。"""

    return forward_signal_apply(
        data,
        rKlineExample,
        param_args=(n,),
        param_kwargs={"field": field},
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineExample", "rKlineExample"]
```

`Kline` 是 Python API 的 family 限定，不应自动加入训练列名。上例的 `full_name` 应继续来自 component，例如 `Example(20)[close]`，而不是 `KlineExample(20)[close]`。

## 必做检查

1. `fields` 必须真实表达算法输入；结构化 HLC 指标不能伪装成单字段指标。
2. 不重复声明 pyta2 已有 schema/window/full name。
3. 所有影响数值的参数必须传入 pyta2 组件，使其进入 component full name；额外 sigma2 参数必须进入最终 full name。
4. rolling 类与 batch 函数放在同一个 canonical 文件并一起导出。
5. 测试 rolling 与 pyta2、batch 与 rolling、`update_last()` 与最终数据重放三组等价性。
6. 多输出因子的 `factor_names` 必须逐项对应 `output_keys`。
7. 新文件加入所属领域包的 `__init__.py` 和 `sigma2/kline/__init__.py`；稳定高频入口再加入顶层 `sigma2/__init__.py`。
8. canonical 类的 `__module__` 必须指向领域目录；兼容路径只能导入转发，不能复制公式。
9. 新 API 不得使用与 pyta2 冲突的短名称，也不得把新功能加入 `compat/`。

复杂因子如果组合多个 pyta2 指标或有市场结构状态，应直接继承 family 基类并显式实现 `forward()`；自身 deque 等额外递推状态必须声明在 `_update_state_fields`，并验证 `update_last()` 重放等价性。
