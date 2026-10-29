from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyta2.volume import rMFI as _rPytaMFI
from pyta2.volume import rOBV as _rPytaOBV
from pyta2.volume import rVWAP as _rPytaVWAP

from sigma2.batch import forward_signal_apply

from .._internal.indicator_factor import _rKlineIndicatorFactor


class rKlineOBV(_rKlineIndicatorFactor):
    """将收盘价和成交量传给 pyta2 OBV。"""

    name = "OBV"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            _rPytaOBV(buffer_size=0), fields=("close", "volume"),
            history_window=2, **kwargs,
        )


class rKlineMFI(_rKlineIndicatorFactor):
    """将典型价格和成交量输入绑定到 pyta2 MFI。"""

    name = "MFI"

    def __init__(self, n: int = 14, **kwargs: Any) -> None:
        indicator = _rPytaMFI(n, buffer_size=0)
        self.n = indicator.n
        super().__init__(
            indicator, fields=("high", "low", "close", "volume"),
            history_window=1, **kwargs,
        )


class rKlineVWAP(_rKlineIndicatorFactor):
    """滚动窗口成交量加权价格；非交易日重置型 VWAP。"""

    name = "VWAP"

    def __init__(self, n: int = 20, *, ma_type: str = "SMA", **kwargs: Any) -> None:
        indicator = _rPytaVWAP(n, ma_type=ma_type, buffer_size=0)
        self.n, self.ma_type = indicator.n, indicator.ma_type
        super().__init__(
            indicator, fields=("high", "low", "close", "volume"),
            history_window=1, **kwargs,
        )


def KlineOBV(
    data: Any, *, return_type: str = "dict", return_meta_info: bool = False,
    symbol: str | None = None, key_map: Mapping[str, str] | None = None,
) -> Any:
    return forward_signal_apply(
        data, rKlineOBV, return_type=return_type, return_meta_info=return_meta_info,
        symbol=symbol, key_map=key_map,
    )


def KlineMFI(
    data: Any, n: int = 14, *, return_type: str = "dict",
    return_meta_info: bool = False, symbol: str | None = None,
    key_map: Mapping[str, str] | None = None,
) -> Any:
    return forward_signal_apply(
        data, rKlineMFI, param_args=(n,), return_type=return_type,
        return_meta_info=return_meta_info, symbol=symbol, key_map=key_map,
    )


def KlineVWAP(
    data: Any, n: int = 20, *, ma_type: str = "SMA",
    return_type: str = "dict", return_meta_info: bool = False,
    symbol: str | None = None, key_map: Mapping[str, str] | None = None,
) -> Any:
    return forward_signal_apply(
        data, rKlineVWAP, param_args=(n,), param_kwargs={"ma_type": ma_type},
        return_type=return_type, return_meta_info=return_meta_info,
        symbol=symbol, key_map=key_map,
    )


__all__ = ["KlineMFI", "KlineOBV", "KlineVWAP", "rKlineMFI", "rKlineOBV", "rKlineVWAP"]
