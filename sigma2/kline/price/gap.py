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
            schema=[("gap", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            n_backward=1,
            history_window=2,
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes) -> float:
        if len(closes) < 2:
            return float("nan")
        previous_close = closes[-2]
        if (
            not (np.isfinite(previous_close) and np.isfinite(opens[-1]))
            or previous_close == 0
        ):
            return float("nan")
        with np.errstate(over="ignore", invalid="ignore"):
            output = opens[-1] / previous_close - 1.0
        return float(output) if np.isfinite(output) else float("nan")

    @property
    def full_name(self) -> str:
        return str(self.name)


def KlineGap(
    data: Any,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbol: str | None = None,
) -> Any:
    """批量 replay :class:`rKlineGap`。"""

    return forward_signal_apply(
        data,
        rKlineGap,
        return_type=return_type,
        return_meta_info=return_meta_info,
        symbol=symbol,
    )


__all__ = ["KlineGap", "rKlineGap"]
