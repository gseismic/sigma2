from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyta2.momentum import rKDJ as _rPytaKDJ

from sigma2.batch import forward_signal_apply

from .._internal.indicator_factor import _rKlineIndicatorFactor


class rKlineKDJ(_rKlineIndicatorFactor):
    """将 K 线输入绑定到 pyta2 KDJ。"""

    name = "KDJ"

    def __init__(
        self, n1: int = 9, n2: int = 3, n3: int = 3, *,
        ktimes: int = 3, dtimes: int = 2, **kwargs: Any
    ) -> None:
        indicator = _rPytaKDJ(n1, n2, n3, ktimes, dtimes, buffer_size=0)
        self.n1, self.n2, self.n3 = indicator.n1, indicator.n2, indicator.n3
        self.ktimes, self.dtimes = indicator.ktimes, indicator.dtimes
        super().__init__(indicator, fields=("high", "low", "close"), **kwargs)


def KlineKDJ(
    data: Any, n1: int = 9, n2: int = 3, n3: int = 3, *,
    ktimes: int = 3, dtimes: int = 2,
    return_type: str = "dict", return_meta_info: bool = False,
    symbol: str | None = None, key_map: Mapping[str, str] | None = None,
) -> Any:
    return forward_signal_apply(
        data, rKlineKDJ, param_args=(n1, n2, n3),
        param_kwargs={"ktimes": ktimes, "dtimes": dtimes},
        return_type=return_type, return_meta_info=return_meta_info,
        symbol=symbol, key_map=key_map,
    )


__all__ = ["KlineKDJ", "rKlineKDJ"]
