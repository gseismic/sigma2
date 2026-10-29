from __future__ import annotations

from collections import deque
from numbers import Real
from typing import Any

import numpy as np
from pyta2.structure.channel import rBoll

from sigma2.kline.signal import rKlineSignal

_FIELDS = frozenset({"open", "high", "low", "close", "volume"})


class rKlineBoll(rKlineSignal):
    """按指定 K 线字段计算布林带，并支持末根 K 线重算。"""

    name = "Boll"

    def __init__(
        self,
        n: int = 20,
        F: Real = 2.0,
        *,
        field: str = "close",
        buffer_size: int = 1,
    ) -> None:
        if not isinstance(field, str) or field not in _FIELDS:
            raise ValueError(f"unsupported K-line field: {field!r}")

        indicator = rBoll(n, F, buffer_size=0, return_dict=True)
        self._field = field
        super().__init__(
            schema=dict(indicator.schema.items()),
            n_backward=indicator.n_backward,
            buffer_size=buffer_size,
            used_fields=(field,),
        )
        self._state.update(
            indicator=indicator,
            values=deque(maxlen=indicator.min_periods),
        )

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
        fields = {
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
        value = fields[self.field]
        values = self._state["values"]
        values.append(float("nan") if value is None else value)
        return self._state["indicator"].rolling(np.asarray(values, dtype=float))

    @property
    def field(self) -> str:
        return self._field

    @property
    def n(self) -> int:
        return self._state["indicator"].n

    @property
    def F(self) -> Real:
        return self._state["indicator"].F

    @property
    def full_name(self) -> str:
        return f"{self._state['indicator'].full_name}[{self.field}]"


__all__ = ["rKlineBoll"]
