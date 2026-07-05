from __future__ import annotations

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.families import rKlineWindowSignal


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
