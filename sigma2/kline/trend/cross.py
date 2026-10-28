from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyta2.relation import rMACross as _rPytaMACross

from sigma2.core import forward_signal_apply

from .._internal.indicator_factor import _rKlineIndicatorFactor


class rKlineMACross(_rKlineIndicatorFactor):
    """复用 pyta2 均线交叉，输出方向和两条均线。"""

    name = "MACross"

    def __init__(
        self, l: int = 5, xl: int = 20, *, ma_type: str = "EMA",  # noqa: E741
        stride: int = 1, field: str = "close", **kwargs: Any
    ) -> None:
        indicator = _rPytaMACross(l, xl, ma_type=ma_type, stride=stride, buffer_size=0)
        self.l, self.xl = indicator.l, indicator.xl
        self.ma_type, self.stride, self.field = indicator.ma_type, indicator.stride, field
        super().__init__(indicator, fields=(field,), **kwargs)


def KlineMACross(
    data: Any, l: int = 5, xl: int = 20, *, ma_type: str = "EMA",  # noqa: E741
    stride: int = 1, field: str = "close",
    return_type: str = "dict", return_meta_info: bool = False,
    symbol: str | None = None, key_map: Mapping[str, str] | None = None,
) -> Any:
    return forward_signal_apply(
        data, rKlineMACross, param_args=(l, xl),
        param_kwargs={"ma_type": ma_type, "stride": stride, "field": field},
        return_type=return_type, return_meta_info=return_meta_info,
        symbol=symbol, key_map=key_map,
    )


__all__ = ["KlineMACross", "rKlineMACross"]
