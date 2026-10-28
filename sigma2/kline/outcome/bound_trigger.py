from __future__ import annotations

from collections import deque
from numbers import Real
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.core import rKlineOutcome

from ..volatility.atr import rKlineATR


class rKlineATRBoundTrigger(rKlineOutcome):
    """用锚点 ATR 定义上下边界，固定观察期后报告首次触发。"""

    name = "kline_atr_bound_trigger"

    def __init__(
        self,
        x_unit_ub: float,
        x_unit_lb: float,
        n_forward: int,
        *,
        symbol: str | None = None,
        atr_n: int = 20,
        atr_ma_type: str = "EMA",
        **kwargs: Any,
    ) -> None:
        n_forward = ensure_integer(n_forward, "n_forward", min_value=1)
        for name, value in (("x_unit_ub", x_unit_ub), ("x_unit_lb", x_unit_lb)):
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not np.isfinite(value)
                or value <= 0
            ):
                raise ValueError(f"{name} must be a finite positive number")
        self.x_unit_ub = float(x_unit_ub)
        self.x_unit_lb = float(x_unit_lb)
        self.atr_n = ensure_integer(atr_n, "atr_n", min_value=1)
        self.atr_ma_type = atr_ma_type
        self._atr = rKlineATR(
            self.atr_n, ma_type=atr_ma_type, symbol=symbol, buffer_size=0
        )
        super().__init__(
            schema={
                "trigger": Scalar(low=-1, high=1, dtype=np.int8),
                "unit_change": Scalar(low=-np.inf, high=np.inf, dtype=np.float64),
                "trigger_index": Scalar(low=-1, high=n_forward, dtype=np.int64),
            },
            symbol=symbol,
            n_backward=self._atr.n_backward,
            n_forward=n_forward,
            **kwargs,
        )

    def reset_extras(self) -> None:
        self._atr.reset()
        self._history = deque(maxlen=self.n_forward + 1)
        self._units = deque(maxlen=self.n_forward + 1)

    def forward(self, bar):
        self._history.append(bar)
        self._units.append(self._atr.step(bar))
        if len(self._history) <= self.n_forward:
            return self.missing_output
        bars = list(self._history)
        anchor, unit = bars[0].close, self._units[0]
        if not (np.isfinite(anchor) and np.isfinite(unit) and unit > 0):
            return self.missing_output
        upper = anchor + self.x_unit_ub * unit
        lower = anchor - self.x_unit_lb * unit
        if not np.isfinite(upper) or not np.isfinite(lower):
            return self.missing_output
        if any(
            not all(
                np.isfinite(value)
                for value in (item.open, item.high, item.low, item.close)
            )
            or item.high < item.low
            or not (item.low <= item.open <= item.high)
            or not (item.low <= item.close <= item.high)
            for item in bars[1:]
        ):
            return self.missing_output
        for offset, item in enumerate(bars[1:], 1):
            up, down = item.high >= upper, item.low <= lower
            if up and down:
                up = item.high - item.open < item.open - item.low
                down = not up
            if up or down:
                return (
                    1 if up else -1,
                    self.x_unit_ub if up else -self.x_unit_lb,
                    offset,
                )
        return 0, 0.0, -1

    @property
    def full_name(self) -> str:
        return (
            f"{self.name}(x_unit_ub={self.x_unit_ub},x_unit_lb={self.x_unit_lb},"
            f"n_forward={self.n_forward},atr_n={self.atr_n},atr_ma_type={self.atr_ma_type})"
        )


__all__ = ["rKlineATRBoundTrigger"]
