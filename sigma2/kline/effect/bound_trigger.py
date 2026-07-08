from __future__ import annotations

from typing import Any

import numpy as np
from pyta2.effect import rBoundTrigger
from pyta2.utils.deque import NumpyDeque
from pyta2.utils.space import Scalar
from pyta2.stats.atr import rATR

from sigma2.core import rKlineWindowSignal


class rKlineATRBoundTrigger(rKlineWindowSignal):
    """基于 ATR 单位的 K 线固定上下边界触发 target。"""

    name = "kline_atr_bound_trigger"

    def __init__(
        self,
        x_unit_ub: float,
        x_unit_lb: float,
        n_forward: int,
        *,
        atr_n: int = 20,
        atr_ma_type: str = "EMA",
        **kwargs: Any,
    ) -> None:
        if x_unit_ub <= 0 or x_unit_lb <= 0:
            raise ValueError(
                "x_unit_ub and x_unit_lb must be greater than 0, "
                f"got {x_unit_ub!r} and {x_unit_lb!r}"
            )
        if n_forward < 1:
            raise ValueError(f"n_forward must be greater than or equal to 1, got {n_forward!r}")
        if atr_n is None or atr_n < 1:
            raise ValueError(f"atr_n must be greater than or equal to 1, got {atr_n!r}")
        self.x_unit_ub = x_unit_ub
        self.x_unit_lb = x_unit_lb
        self.n_forward = n_forward
        self.atr_n = atr_n
        self.atr_ma_type = atr_ma_type
        self._trigger_window = n_forward + 1
        self._atr = rATR(atr_n, ma_type=atr_ma_type, buffer_size=1, return_dict=False)
        self._units = NumpyDeque(maxlen=self._trigger_window)
        super().__init__(
            window=atr_n + n_forward,
            schema={
                "trigger": Scalar(low=-1, high=1, dtype="int8"),
                "unit_change": Scalar(low=-float("inf"), high=float("inf"), dtype="float64"),
                "trigger_index": Scalar(low=-1, high=np.iinfo(np.int64).max, dtype="int64"),
            },
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        self._atr.reset()
        self._units.clear()

    def forward(self, opens, highs, lows, closes, volumes) -> Any:
        self._units.append(self._atr.rolling(highs, lows, closes))
        trigger_effect = self._make_trigger_effect()
        return trigger_effect.backward(
            self._units.values,
            opens[-self._trigger_window :],
            highs[-self._trigger_window :],
            lows[-self._trigger_window :],
            closes[-self._trigger_window :],
        )

    @property
    def full_name(self) -> str:
        return (
            f"{self.name}(x_unit_ub={self.x_unit_ub},x_unit_lb={self.x_unit_lb},"
            f"n_forward={self.n_forward},atr_n={self.atr_n},atr_ma_type={self.atr_ma_type})"
        )

    def _make_trigger_effect(self):
        return rBoundTrigger(
            self.x_unit_ub,
            self.x_unit_lb,
            self.n_forward,
            buffer_size=1,
            return_dict=False,
        )
