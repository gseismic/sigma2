from __future__ import annotations

from typing import Any

import numpy as np
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.core import rKlineWindowOutcome
from sigma2.utils.pyta2 import normalize_pyta2_inputs


class rKlineFutureChange(rKlineWindowOutcome):
    """计算锚点到未来末端的绝对变化，要求完整未来区间有效。"""

    name = "kline_future_change"

    def __init__(self, n_forward: int, *, field: str = "close", **kwargs: Any) -> None:
        n_forward = ensure_integer(n_forward, "n_forward", min_value=1)
        self.field = normalize_pyta2_inputs((field,))[0]
        super().__init__(
            schema={"value": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            n_backward=0,
            n_forward=n_forward,
            history_window=n_forward + 1,
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes) -> float:
        if len(closes) <= self.n_forward:
            return float("nan")
        values = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }[self.field]
        anchor, end = values[0], values[-1]
        if not np.all(np.isfinite(values)):
            return float("nan")
        with np.errstate(over="ignore", invalid="ignore"):
            output = end - anchor
        return float(output) if np.isfinite(output) else float("nan")

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.field},{self.n_forward})"


__all__ = ["rKlineFutureChange"]
