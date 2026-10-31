from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
from pyta2.momentum import rRSI

from sigma2.core.utils import forward_step_apply
from sigma2.kline.signal import rKlineSignal

_FIELDS = frozenset({"open", "high", "low", "close", "volume"})


class rKlineRSI(rKlineSignal):
    """按指定 K 线字段计算相对强弱指标。"""

    name = "RSI"

    def __init__(
        self,
        n: int = 14,
        *,
        field: str = "close",
        buffer_size: int = 1,
    ) -> None:
        if not isinstance(field, str) or field not in _FIELDS:
            raise ValueError(f"unsupported K-line field: {field!r}")
        indicator = rRSI(n, buffer_size=0, return_dict=True)
        self._field = field
        super().__init__(
            schema=dict(indicator.schema.items()),
            n_backward=indicator.n_backward,
            buffer_size=buffer_size,
            used_fields=(field,),
        )
        self._indicator = indicator
        self._values = deque(maxlen=indicator.min_periods)

    def forward(
        self,
        open,
        high,
        low,
        close,
        volume=None,
        *,
        open_time=None,
        is_missing=False,
    ) -> dict[str, Any]:
        value = {
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }[self.field]
        values = self._values
        values.append(float("nan") if value is None else value)
        return self._indicator.rolling(np.asarray(values, dtype=float))

    @property
    def field(self) -> str:
        return self._field

    @property
    def n(self) -> int:
        return self._indicator.n

    @property
    def full_name(self) -> str:
        return f"{self._indicator.full_name}[{self.field}]"


def KlineRSI(
    data: Iterable[Mapping[str, Any]],
    n: int = 14,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """逐条重放 K 线并输出 RSI。"""
    return forward_step_apply(
        data,
        rKlineRSI(n, field=field, buffer_size=0),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineRSI", "rKlineRSI"]
