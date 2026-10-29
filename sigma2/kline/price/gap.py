from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.core.utils import forward_step_apply
from sigma2.kline.signal import rKlineSignal


class rKlineGap(rKlineSignal):
    """当前 open 相对上一根 close 的跳空幅度。"""

    name = "gap"
    full_name = "gap"

    def __init__(self, *, buffer_size: int = 1) -> None:
        super().__init__(
            schema={"gap": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            n_backward=1,
            buffer_size=buffer_size,
            used_fields=("open", "close"),
        )
        self._state["previous_close"] = float("nan")

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
    ) -> dict[str, float]:
        previous = self._state["previous_close"]
        self._state["previous_close"] = close
        if not (np.isfinite(previous) and np.isfinite(open)) or previous == 0:
            return {"gap": float("nan")}
        with np.errstate(over="ignore", invalid="ignore"):
            result = open / previous - 1.0
        return {"gap": float(result) if np.isfinite(result) else float("nan")}


def KlineGap(
    data: Iterable[Mapping[str, Any]],
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """逐条重放 K 线并输出跳空幅度。"""
    return forward_step_apply(
        data,
        rKlineGap(buffer_size=0),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineGap", "rKlineGap"]
