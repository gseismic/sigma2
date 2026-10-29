from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
from pyta2.volume import rMFI, rOBV, rVWAP

from sigma2.core.utils import forward_step_apply
from sigma2.kline.signal import rKlineSignal

_MA_TYPES = frozenset({"SMA", "EMA", "WMA", "HMA", "DEMA", "TEMA", "ZLEMA"})


class rKlineOBV(rKlineSignal):
    """使用收盘价和成交量计算 OBV。"""

    name = "OBV"

    def __init__(self, *, buffer_size: int = 1) -> None:
        indicator = rOBV(buffer_size=0, return_dict=True)
        super().__init__(
            schema=dict(indicator.schema.items()),
            n_backward=indicator.n_backward,
            buffer_size=buffer_size,
            used_fields=("close", "volume"),
        )
        self._state.update(indicator=indicator, closes=deque(maxlen=2))

    def forward(
        self,
        open,
        high,
        low,
        close,
        volume=None,
        *,
        open_time=None,
        is_closed=True,
        is_missing=False,
    ) -> dict[str, Any]:
        closes = self._state["closes"]
        closes.append(close)
        volume = float("nan") if volume is None else volume
        return self._state["indicator"].rolling(
            np.asarray(closes, dtype=float), (volume,)
        )

    @property
    def full_name(self) -> str:
        return f"{self._state['indicator'].full_name}[close,volume]"


class rKlineMFI(rKlineSignal):
    """使用典型价格和成交量计算资金流量指数。"""

    name = "MFI"

    def __init__(self, n: int = 14, *, buffer_size: int = 1) -> None:
        indicator = rMFI(n, buffer_size=0, return_dict=True)
        super().__init__(
            schema=dict(indicator.schema.items()),
            n_backward=indicator.n_backward,
            buffer_size=buffer_size,
            used_fields=("high", "low", "close", "volume"),
        )
        self._state["indicator"] = indicator

    def forward(
        self,
        open,
        high,
        low,
        close,
        volume=None,
        *,
        open_time=None,
        is_closed=True,
        is_missing=False,
    ) -> dict[str, Any]:
        volume = float("nan") if volume is None else volume
        return self._state["indicator"].rolling((high,), (low,), (close,), (volume,))

    @property
    def n(self) -> int:
        return self._state["indicator"].n

    @property
    def full_name(self) -> str:
        return f"{self._state['indicator'].full_name}[high,low,close,volume]"


class rKlineVWAP(rKlineSignal):
    """滚动窗口成交量加权价格，不按交易日重置。"""

    name = "VWAP"

    def __init__(
        self, n: int = 20, *, ma_type: str = "SMA", buffer_size: int = 1
    ) -> None:
        if not isinstance(ma_type, str):
            raise TypeError("ma_type must be a string")
        ma_type = ma_type.strip().upper()
        if ma_type not in _MA_TYPES:
            raise ValueError(f"unsupported single-parameter MA: {ma_type}")
        indicator = rVWAP(n, ma_type=ma_type, buffer_size=0, return_dict=True)
        super().__init__(
            schema=dict(indicator.schema.items()),
            n_backward=indicator.n_backward,
            buffer_size=buffer_size,
            used_fields=("high", "low", "close", "volume"),
        )
        self._state["indicator"] = indicator

    def forward(
        self,
        open,
        high,
        low,
        close,
        volume=None,
        *,
        open_time=None,
        is_closed=True,
        is_missing=False,
    ) -> dict[str, Any]:
        volume = float("nan") if volume is None else volume
        return self._state["indicator"].rolling((high,), (low,), (close,), (volume,))

    @property
    def n(self) -> int:
        return self._state["indicator"].n

    @property
    def ma_type(self) -> str:
        return self._state["indicator"].ma_type

    @property
    def full_name(self) -> str:
        return f"{self._state['indicator'].full_name}[high,low,close,volume]"


def KlineOBV(
    data: Iterable[Mapping[str, Any]],
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    return forward_step_apply(
        data,
        rKlineOBV(buffer_size=0),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


def KlineMFI(
    data: Iterable[Mapping[str, Any]],
    n: int = 14,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    return forward_step_apply(
        data,
        rKlineMFI(n, buffer_size=0),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


def KlineVWAP(
    data: Iterable[Mapping[str, Any]],
    n: int = 20,
    *,
    ma_type: str = "SMA",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    return forward_step_apply(
        data,
        rKlineVWAP(n, ma_type=ma_type, buffer_size=0),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineMFI", "KlineOBV", "KlineVWAP", "rKlineMFI", "rKlineOBV", "rKlineVWAP"]
