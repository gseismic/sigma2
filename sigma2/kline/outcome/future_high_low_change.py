from __future__ import annotations

from typing import Any

import numpy as np
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.kline._internal.data import include_required_fields
from sigma2.kline.window import rKlineWindowOutcome
from sigma2.utils.pyta2 import normalize_pyta2_inputs


class rKlineFutureHighLowChange(rKlineWindowOutcome):
    """计算未来窗口的最高价和最低价相对锚点的变化。"""

    name = "kline_future_high_low_change"

    def __init__(
        self, n_forward: int, *, reference_field: str = "close", **kwargs: Any
    ) -> None:
        n_forward = ensure_integer(n_forward, "n_forward", min_value=1)
        self.reference_field = normalize_pyta2_inputs((reference_field,))[0]
        include_required_fields(kwargs, self.reference_field)
        super().__init__(
            schema={
                key: Scalar(low=-np.inf, high=np.inf, dtype=np.float64)
                for key in ("high_change", "low_change")
            },
            n_backward=0,
            n_forward=n_forward,
            history_window=n_forward + 1,
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes):
        result = [np.nan, np.nan]
        if len(closes) <= self.n_forward:
            return tuple(result)
        values = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }[self.reference_field]
        anchor = values[0]
        if not np.isfinite(anchor):
            return tuple(result)
        for index, future in enumerate((highs[1:], lows[1:])):
            if np.all(np.isfinite(future)):
                extreme = np.max(future) if index == 0 else np.min(future)
                with np.errstate(over="ignore", invalid="ignore"):
                    value = extreme - anchor
                result[index] = float(value) if np.isfinite(value) else np.nan
        return tuple(result)

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.reference_field},{self.n_forward})"


__all__ = ["rKlineFutureHighLowChange"]
