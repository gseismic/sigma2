from __future__ import annotations

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.core import rKlineWindowSignal


class rGap(rKlineWindowSignal):
    """当前 open 相对上一根 close 的跳空幅度。"""

    name = "gap"

    def __init__(self, **kwargs) -> None:
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
