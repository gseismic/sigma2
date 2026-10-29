from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np
from pyta2.stats.atr import rATR

from sigma2.kline.signal import rKlineSignal

_MA_TYPES = frozenset({"SMA", "EMA", "WMA", "HMA", "DEMA", "TEMA", "ZLEMA"})


class rKlineATR(rKlineSignal):
    """计算 ATR，并支持末根 K 线重算。"""

    name = "ATR"

    def __init__(
        self,
        n: int = 20,
        *,
        ma_type: str = "EMA",
        buffer_size: int = 1,
    ) -> None:
        if not isinstance(ma_type, str):
            raise TypeError("ma_type must be a string")
        ma_type = ma_type.strip().upper()
        if ma_type not in _MA_TYPES:
            raise ValueError(f"unsupported single-parameter MA: {ma_type}")

        indicator = rATR(n, ma_type=ma_type, buffer_size=0, return_dict=True)
        super().__init__(
            schema=dict(indicator.schema.items()),
            n_backward=indicator.n_backward,
            buffer_size=buffer_size,
            used_fields=("high", "low", "close"),
        )
        # ATR 需要当前 HLC 和上一根的收盘价。
        self._state.update(indicator=indicator, values=deque(maxlen=2))

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
        values = self._state["values"]
        values.append((high, low, close))
        hlc = np.asarray(values, dtype=float)
        return self._state["indicator"].rolling(hlc[:, 0], hlc[:, 1], hlc[:, 2])

    @property
    def n(self) -> int:
        return self._state["indicator"].n

    @property
    def ma_type(self) -> str:
        return self._state["indicator"].ma_type

    @property
    def full_name(self) -> str:
        return f"{self._state['indicator'].full_name}[high,low,close]"


__all__ = ["rKlineATR"]
