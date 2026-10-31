from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
from pyta2.relation import rMACross

from sigma2.core.utils import forward_step_apply
from sigma2.kline.signal import rKlineSignal

_MA_TYPES = frozenset({"SMA", "EMA", "WMA", "HMA", "DEMA", "TEMA", "ZLEMA"})
_FIELDS = frozenset({"open", "high", "low", "close", "volume"})


class rKlineMACross(rKlineSignal):
    """计算两条均线的交叉方向及其数值。"""

    name = "MACross"

    def __init__(
        self,
        fast: int = 5,
        slow: int = 20,
        *,
        ma_type: str = "EMA",
        stride: int = 1,
        field: str = "close",
        buffer_size: int = 1,
    ) -> None:
        if not isinstance(ma_type, str):
            raise TypeError("ma_type must be a string")
        ma_type = ma_type.strip().upper()
        if ma_type not in _MA_TYPES:
            raise ValueError(f"unsupported single-parameter MA: {ma_type}")
        if not isinstance(field, str) or field not in _FIELDS:
            raise ValueError(f"unsupported K-line field: {field!r}")
        indicator = rMACross(
            fast, slow, ma_type=ma_type, stride=stride, buffer_size=0, return_dict=True
        )
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
    def fast(self) -> int:
        return self._indicator.l

    @property
    def slow(self) -> int:
        return self._indicator.xl

    @property
    def ma_type(self) -> str:
        return self._indicator.ma_type

    @property
    def stride(self) -> int:
        return self._indicator.stride

    @property
    def full_name(self) -> str:
        return f"{self._indicator.full_name}[{self.field}]"


def KlineMACross(
    data: Iterable[Mapping[str, Any]],
    fast: int = 5,
    slow: int = 20,
    *,
    ma_type: str = "EMA",
    stride: int = 1,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """逐条重放 K 线并输出均线交叉。"""
    return forward_step_apply(
        data,
        rKlineMACross(
            fast, slow, ma_type=ma_type, stride=stride, field=field, buffer_size=0
        ),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineMACross", "rKlineMACross"]
