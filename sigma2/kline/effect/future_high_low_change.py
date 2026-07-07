from __future__ import annotations

from typing import Any

import numpy as np
from pyta2.effect import rFutureHighChange, rFutureLowChange
from pyta2.utils.space import Scalar

from sigma2.core import rKlineWindowSignal
from sigma2.utils.pyta2 import normalize_pyta2_inputs


class rKlineFutureHighLowChange(rKlineWindowSignal):
    """未来最高价和最低价相对参考字段的路径变动。"""

    name = "kline_future_high_low_change"

    def __init__(
        self,
        horizon: int,
        *,
        reference_field: str = "close",
        **kwargs: Any,
    ) -> None:
        self.horizon = horizon
        self.reference_field = normalize_pyta2_inputs((reference_field,))[0]
        self._high_effect = rFutureHighChange(horizon, buffer_size=1)
        self._low_effect = rFutureLowChange(horizon, buffer_size=1)
        super().__init__(
            window=horizon + 1,
            schema=[
                ("high_change", Scalar(low=-np.inf, high=np.inf, dtype=np.float64)),
                ("low_change", Scalar(low=-np.inf, high=np.inf, dtype=np.float64)),
            ],
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        self._high_effect = rFutureHighChange(self.horizon, buffer_size=1)
        self._low_effect = rFutureLowChange(self.horizon, buffer_size=1)

    def forward(self, opens, highs, lows, closes, volumes):
        references = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }[self.reference_field]
        return (
            self._high_effect.backward(highs, references),
            self._low_effect.backward(lows, references),
        )

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.reference_field},{self.horizon})"
