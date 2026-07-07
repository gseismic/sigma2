from __future__ import annotations

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.core import rKlineWindowSignal


class rReturn(rKlineWindowSignal):
    """基于 close 的 n 根 K 线收益率。"""

    name = "return"

    def __init__(self, n: int = 1, **kwargs) -> None:
        if n <= 0:
            raise ValueError(f"n must be greater than 0, got {n}")
        self.n = n
        super().__init__(
            window=n + 1,
            schema=[("return", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes) -> float:
        if len(closes) <= self.n:
            return float("nan")
        previous = closes[-self.n - 1]
        if previous == 0:
            return float("nan")
        return float(closes[-1] / previous - 1.0)

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.n})"
