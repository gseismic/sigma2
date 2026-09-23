from __future__ import annotations

from typing import Any

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.core import forward_signal_apply, rKlineWindowSignal


class rKlineGap(rKlineWindowSignal):
    """当前 open 相对上一根 close 的跳空幅度。"""

    name = "gap"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            window=2,
            schema=[("gap", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes) -> float:
        if len(closes) < 2:
            return float("nan")
        previous_close = closes[-2]
        if previous_close == 0:
            return float("nan")
        return float(opens[-1] / previous_close - 1.0)

    @property
    def full_name(self) -> str:
        return str(self.name)


def KlineGap(
    data: Any,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """批量 replay :class:`rKlineGap`。"""

    return forward_signal_apply(
        data,
        rKlineGap,
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineGap", "rKlineGap"]
