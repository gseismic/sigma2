from __future__ import annotations

from typing import Any

import numpy as np
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.core import rKlineWindowOutcome
from sigma2.utils.pyta2 import normalize_pyta2_inputs


class rKlineFutureReturn(rKlineWindowOutcome):
    """计算锚点到未来末端的收益，要求完整未来区间有效。"""

    name = "kline_future_return"

    def __init__(
        self,
        n_forward: int,
        *,
        field: str = "close",
        return_type: str = "simple",
        **kwargs: Any,
    ) -> None:
        n_forward = ensure_integer(n_forward, "n_forward", min_value=1)
        if not isinstance(return_type, str) or return_type.lower() not in {
            "simple",
            "log",
        }:
            raise ValueError("return_type must be 'simple' or 'log'")
        self.return_type = return_type.lower()
        self.field = normalize_pyta2_inputs((field,))[0]
        key = "log_return" if self.return_type == "log" else "return"
        super().__init__(
            schema={key: Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
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
        if not np.all(np.isfinite(values)) or anchor == 0:
            return float("nan")
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            ratio = end / anchor
            if self.return_type == "log":
                output = np.log(ratio) if ratio > 0 else np.nan
            else:
                output = ratio - 1.0
        return float(output) if np.isfinite(output) else float("nan")

    @property
    def full_name(self) -> str:
        return (
            f"{self.name}({self.field},{self.n_forward},return_type={self.return_type})"
        )


__all__ = ["rKlineFutureReturn"]
