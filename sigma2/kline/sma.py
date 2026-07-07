from __future__ import annotations

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.core import rKlineWindowSignal


class rSMA(rKlineWindowSignal):
    """某个 K 线字段的简单移动平均。"""

    name = "sma"
    supported_fields = ("open", "high", "low", "close", "volume")

    def __init__(self, n: int, field: str = "close", **kwargs) -> None:
        if n <= 0:
            raise ValueError(f"n must be greater than 0, got {n}")
        if field not in self.supported_fields:
            raise ValueError(f"field must be one of {self.supported_fields}, got {field!r}")
        self.n = n
        self.field = field
        super().__init__(
            window=n,
            schema=[("sma", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes) -> float:
        values = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }[self.field]
        if len(values) < self.n:
            return float("nan")
        return float(np.mean(values[-self.n :]))

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.field},{self.n})"
