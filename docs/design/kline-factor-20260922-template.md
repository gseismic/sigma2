# K 线因子文件模板

更新时间：2026-09-22 22:36 CST

状态：已随 `PLAN-018` 验证，配套 `docs/design/sigma2-20260922-v5.md` v5.1

目标：新增一个由单个 pyta2 rolling 指标支撑的 K 线因子时，保持“一个因子一个文件、rolling/batch 同文件、计算公式只有一份”。

## 文件模板

推荐复制为 `sigma2/kline/example.py`，再替换类名、函数名和 pyta2 组件：

```python
from pyta2 import rExample as _rPytaExample

from sigma2.core import forward_signal_apply

from ._factor import _rKlineIndicatorFactor


class rExample(_rKlineIndicatorFactor):
    """Example K 线因子。"""

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
            _rPytaExample(n, buffer_size=0),
            fields=(field,),
            **kwargs,
        )


def Example(
    data,
    n: int = 20,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
):
    """批量 replay ``rExample``。"""

    return forward_signal_apply(
        data,
        rExample,
        param_args=(n,),
        param_kwargs={"field": field},
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["rExample", "Example"]
```

## 必做检查

1. `fields` 必须真实表达算法输入；结构化 HLC 指标不能伪装成单字段指标。
2. 不重复声明 pyta2 已有 schema/window/full name。
3. 所有影响数值的参数必须传入 pyta2 组件，使其进入 component full name；额外 sigma 参数必须进入最终 full name。
4. rolling 类与 batch 函数放在同一个文件并一起导出。
5. 测试 rolling 与 pyta2、batch 与 rolling、`update_last()` 与最终数据重放三组等价性。
6. 多输出因子的 `factor_names` 必须逐项对应 `output_keys`。
7. 新文件加入 `sigma2/kline/__init__.py`；只有稳定高频入口才进一步加入 `sigma2/__init__.py`。

复杂因子如果组合多个 pyta2 指标或有市场结构状态，应直接继承 family 基类并显式实现 `forward()`；不要为了套模板而隐藏业务逻辑。
