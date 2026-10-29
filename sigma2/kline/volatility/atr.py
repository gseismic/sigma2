from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyta2.stats.atr import rATR as _rPytaATR

from sigma2.batch import forward_signal_apply

from .._internal.indicator_factor import _rKlineIndicatorFactor


class rKlineATR(_rKlineIndicatorFactor):
    """将 K 线输入绑定到 pyta2 ATR。"""

    name = "ATR"

    def __init__(self, n: int = 20, *, ma_type: str = "EMA", **kwargs: Any) -> None:
        indicator = _rPytaATR(n, ma_type=ma_type, buffer_size=0)
        self.n, self.ma_type = indicator.n, indicator.ma_type
        super().__init__(
            indicator, fields=("high", "low", "close"), history_window=2, **kwargs
        )


def KlineATR(
    data: Any, n: int = 20, *, ma_type: str = "EMA",
    return_type: str = "dict", return_meta_info: bool = False,
    symbol: str | None = None, key_map: Mapping[str, str] | None = None,
) -> Any:
    return forward_signal_apply(
        data, rKlineATR, param_args=(n,), param_kwargs={"ma_type": ma_type},
        return_type=return_type, return_meta_info=return_meta_info,
        symbol=symbol, key_map=key_map,
    )


__all__ = ["KlineATR", "rKlineATR"]
