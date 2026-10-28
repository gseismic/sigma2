from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np
from pyta2.trend.ma.api import get_ma_class
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply, rKlineWindowSignal
from sigma2.core._indicator_factor import rolling_with_nan_recovery


class rKlineATR(rKlineWindowSignal):
    """计算单 symbol 真实波幅并用 pyta2 均线平滑。"""

    name = "ATR"

    def __init__(self, n: int = 20, *, ma_type: str = "EMA", **kwargs: Any) -> None:
        self.n = ensure_integer(n, "n", min_value=1)
        self._ma = get_ma_class(ma_type)(self.n, buffer_size=0, return_dict=False)
        self.ma_type = str(self._ma.name)
        super().__init__(
            schema={"atr": Scalar(low=0, high=np.inf, dtype=np.float64)},
            n_backward=self._ma.n_backward,
            history_window=2,
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        self._ma.reset()
        self._ranges = deque(maxlen=self._ma.min_periods)

    def forward(self, opens, highs, lows, closes, volumes) -> float:
        high, low = highs[-1], lows[-1]
        if not (np.isfinite(high) and np.isfinite(low)) or high < low:
            tr = np.nan
        elif len(closes) == 1:
            tr = high - low
        elif not np.isfinite(closes[-2]):
            tr = np.nan
        else:
            previous = closes[-2]
            tr = max(high - low, abs(high - previous), abs(low - previous))
        self._ranges.append(tr)
        return float(
            rolling_with_nan_recovery(self._ma, np.asarray(self._ranges, dtype=float))
        )

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.n},{self.ma_type})[high,low,close]"


def KlineATR(
    data: Any,
    n: int = 20,
    *,
    ma_type: str = "EMA",
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbol: str | None = None,
) -> Any:
    """逐时点重放 ATR。"""
    return forward_signal_apply(
        data,
        rKlineATR,
        param_args=(n,),
        param_kwargs={"ma_type": ma_type},
        return_type=return_type,
        return_meta_info=return_meta_info,
        symbol=symbol,
    )


__all__ = ["KlineATR", "rKlineATR"]
