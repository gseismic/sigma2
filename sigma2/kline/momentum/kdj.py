from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
from pyta2.momentum import rKDJ

from sigma2.core.utils import forward_step_apply
from sigma2.kline.signal import rKlineSignal


class rKlineKDJ(rKlineSignal):
    """使用最高、最低和收盘价计算 KDJ。"""

    name = "KDJ"

    def __init__(
        self,
        n1: int = 9,
        n2: int = 3,
        n3: int = 3,
        *,
        ktimes: int = 3,
        dtimes: int = 2,
        buffer_size: int = 1,
    ) -> None:
        indicator = rKDJ(n1, n2, n3, ktimes, dtimes, buffer_size=0, return_dict=True)
        super().__init__(
            schema=dict(indicator.schema.items()),
            n_backward=indicator.n_backward,
            buffer_size=buffer_size,
            used_fields=("high", "low", "close"),
        )
        self._state.update(
            indicator=indicator, values=deque(maxlen=indicator.min_periods)
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
        values = self._state["values"]
        values.append((high, low, close))
        hlc = np.asarray(values, dtype=float)
        return self._state["indicator"].rolling(hlc[:, 0], hlc[:, 1], hlc[:, 2])

    @property
    def n1(self) -> int:
        return self._state["indicator"].n1

    @property
    def n2(self) -> int:
        return self._state["indicator"].n2

    @property
    def n3(self) -> int:
        return self._state["indicator"].n3

    @property
    def ktimes(self) -> int:
        return self._state["indicator"].ktimes

    @property
    def dtimes(self) -> int:
        return self._state["indicator"].dtimes

    @property
    def full_name(self) -> str:
        return f"{self._state['indicator'].full_name}[high,low,close]"


def KlineKDJ(
    data: Iterable[Mapping[str, Any]],
    n1: int = 9,
    n2: int = 3,
    n3: int = 3,
    *,
    ktimes: int = 3,
    dtimes: int = 2,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """逐条重放 K 线并输出 KDJ。"""
    return forward_step_apply(
        data,
        rKlineKDJ(n1, n2, n3, ktimes=ktimes, dtimes=dtimes, buffer_size=0),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineKDJ", "rKlineKDJ"]
