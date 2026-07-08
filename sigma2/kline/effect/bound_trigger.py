from __future__ import annotations

from typing import Any

import numpy as np
from pyta2.effect import rBoundTrigger
from pyta2.utils.deque import NumpyDeque
from pyta2.utils.space import Scalar
from pyta2.stats.atr import rATR

from sigma2.core import rKlineWindowSignal


class rKlineATRBoundTrigger(rKlineWindowSignal):
    """K 线固定上下边界触发 target。"""

    name = "kline_bound_trigger"

    def __init__(
        self,
        x_unit_ub: float,
        x_unit_lb: float,
        n_forward: int,
        *,
        unit: str = "atr",
        atr_n: int | None = None,
        atr_ma_type: str = "EMA",
        **kwargs: Any,
    ) -> None:
        unit = unit.lower()
        if unit not in {"atr", "open", "high", "low", "close", "volume"}:
            raise ValueError(
                "unit must be one of 'atr', 'open', 'high', 'low', 'close', 'volume', "
                f"got {unit!r}"
            )
        self.x_unit_ub = x_unit_ub
        self.x_unit_lb = x_unit_lb
        self.n_forward = n_forward
        self.unit = unit
        self.atr_ma_type = atr_ma_type
        if unit == "atr":
            self.atr_n = 20 if atr_n is None else atr_n
            self._atr = rATR(self.atr_n, ma_type=atr_ma_type, buffer_size=1, return_dict=False)
            window = max(n_forward + 1, self.atr_n)
            self._units = NumpyDeque(maxlen=window)
        else:
            self.atr_n = None
            self._atr = None
            window = n_forward + 1
        self._units = NumpyDeque(maxlen=window)
        super().__init__(
            window=window,
            schema={
                "trigger": Scalar(low=-1, high=1, dtype="int8"),
                "unit_change": Scalar(low=-float("inf"), high=float("inf"), dtype="float64"),
                "trigger_index": Scalar(low=-1, high=np.iinfo(np.int64).max, dtype="int64"),
            },
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        if self._atr is not None:
            self._atr.reset()
        self._units.clear()

    def forward(self, opens, highs, lows, closes, volumes) -> Any:
        self._units.append(self._resolve_unit(opens, highs, lows, closes, volumes))
        trigger_effect = self._make_trigger_effect()
        return trigger_effect.backward(self._units.values, opens, highs, lows, closes)

    @property
    def full_name(self) -> str:
        return (
            f"{self.name}(unit={self.unit},x_unit_ub={self.x_unit_ub},"
            f"x_unit_lb={self.x_unit_lb},n_forward={self.n_forward})"
        )

    def _make_trigger_effect(self):
        return rBoundTrigger(
            self.x_unit_ub,
            self.x_unit_lb,
            self.n_forward,
            buffer_size=1,
            return_dict=False,
        )

    def _resolve_unit(self, opens, highs, lows, closes, volumes):
        if self.unit == "atr":
            return self._atr.rolling(highs, lows, closes)

        series = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }[self.unit]
        return series[-1]


rKlineBoundTrigger = rKlineATRBoundTrigger
