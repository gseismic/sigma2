from __future__ import annotations

from typing import Any

from pyta2.momentum import rRSI as _rPytaRSI
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply

from .._internal.indicator_factor import _rKlineIndicatorFactor


class rKlineRSI(_rKlineIndicatorFactor):
    """绑定到一个 K 线字段的相对强弱 Signal。"""

    name = "RSI"

    def __init__(
        self,
        n: int = 14,
        *,
        field: str = "close",
        **kwargs: Any,
    ) -> None:
        self.n = ensure_integer(n, "n", min_value=1)
        self.field = field
        super().__init__(
            _rPytaRSI(self.n, buffer_size=0, return_dict=False),
            fields=(field,),
            **kwargs,
        )


def KlineRSI(
    data: Any,
    n: int = 14,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """批量 replay :class:`rKlineRSI`。"""

    return forward_signal_apply(
        data,
        rKlineRSI,
        param_args=(n,),
        param_kwargs={"field": field},
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineRSI", "rKlineRSI"]
