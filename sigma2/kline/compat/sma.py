from __future__ import annotations

import numpy as np
from pyta2.trend.ma.api import get_ma_class
from pyta2.utils.space import Scalar

from .._internal.indicator_factor import _rKlineIndicatorFactor
from ._warnings import warn_deprecated


class rSMA(_rKlineIndicatorFactor):
    """兼容旧 schema 的 SMA；新代码使用 ``rKlineMA(ma_type='SMA')``。"""

    name = "sma"
    supported_fields = ("open", "high", "low", "close", "volume")

    def __init__(self, n: int, field: str = "close", **kwargs) -> None:
        warn_deprecated("rSMA", "rKlineMA(..., ma_type='SMA')")
        if n <= 0:
            raise ValueError(f"n must be greater than 0, got {n}")
        if field not in self.supported_fields:
            raise ValueError(f"field must be one of {self.supported_fields}, got {field!r}")
        self.n = n
        self.field = field
        indicator = get_ma_class("SMA")(
            n,
            buffer_size=0,
            return_dict=False,
        )
        super().__init__(
            indicator,
            fields=(field,),
            schema=[("sma", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            **kwargs,
        )

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.field},{self.n})"


__all__ = ["rSMA"]
