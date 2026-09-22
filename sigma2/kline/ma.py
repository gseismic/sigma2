from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyta2.trend.ma.api import get_ma_class
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply

from ._factor import _rKlineIndicatorFactor


class rMA(_rKlineIndicatorFactor):
    """可选择均值类型与 K 线字段的通用移动平均因子。"""

    name = "MA"

    def __init__(
        self,
        n: int,
        *,
        ma_type: str = "SMA",
        field: str = "close",
        ma_kwargs: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.n = ensure_integer(n, "n", min_value=1)
        if ma_kwargs is not None and not isinstance(ma_kwargs, Mapping):
            raise TypeError(
                f"ma_kwargs must be a mapping or None, got {type(ma_kwargs).__name__}"
            )
        component_kwargs = dict(ma_kwargs or {})
        forbidden = {
            "buffer_size",
            "return_dict",
            "buffer_factor",
            "extra_window",
            "n",
            "n1",
        } & component_kwargs.keys()
        if forbidden:
            raise ValueError(
                "ma_kwargs must not override lifecycle or primary window arguments: "
                f"{sorted(forbidden)}"
            )

        ma_cls = get_ma_class(ma_type)
        indicator = ma_cls(
            self.n,
            buffer_size=0,
            return_dict=False,
            **component_kwargs,
        )
        self.ma_type = str(indicator.name)
        self.field = field
        self.ma_kwargs = component_kwargs
        super().__init__(indicator, fields=(field,), **kwargs)

    @property
    def full_name(self) -> str:
        component_name = self._indicator.full_name
        # pyta2 当前 KAMA full_name 已含 n1/n2/n3，但未含会改变结果的 stride。
        # sigma2 的训练列名必须把非默认 stride 纳入身份。
        if self.ma_type == "KAMA" and self._indicator.stride != 1:
            component_name = (
                f"{component_name[:-1]},stride={self._indicator.stride})"
            )
        return f"{component_name}[{','.join(self.fields)}]"


def MA(
    data: Any,
    n: int,
    *,
    ma_type: str = "SMA",
    field: str = "close",
    ma_kwargs: Mapping[str, Any] | None = None,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """批量 replay :class:`rMA`。"""

    return forward_signal_apply(
        data,
        rMA,
        param_args=(n,),
        param_kwargs={
            "ma_type": ma_type,
            "field": field,
            "ma_kwargs": ma_kwargs,
        },
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["MA", "rMA"]
