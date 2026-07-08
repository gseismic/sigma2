from __future__ import annotations

from typing import Any

import numpy as np
from pyta2.effect import rBoundTrigger
from pyta2.utils.space import Scalar

from .base import rKlineEffectSignal


class rKlineBoundTrigger(rKlineEffectSignal):
    """K 线固定上下边界触发 target。"""

    name = "kline_bound_trigger"

    def __init__(
        self,
        x_unit_ub: float,
        x_unit_lb: float,
        n_forward: int,
        *,
        unit_field: str = "close",
        **kwargs: Any,
    ) -> None:
        self.x_unit_ub = x_unit_ub
        self.x_unit_lb = x_unit_lb
        self.n_forward = n_forward
        self.unit_field = unit_field
        super().__init__(
            rBoundTrigger,
            effect_args=(x_unit_ub, x_unit_lb, n_forward),
            inputs=(unit_field, "open", "high", "low", "close"),
            schema={
                "trigger": Scalar(low=-1, high=1, dtype="int8"),
                "unit_change": Scalar(low=-float("inf"), high=float("inf"), dtype="float64"),
                "trigger_index": Scalar(low=-1, high=np.iinfo(np.int64).max, dtype="int64"),
            },
            output_transform=self._transform_output,
            full_name=(
                f"{self.name}(unit_field={unit_field},x_unit_ub={x_unit_ub},"
                f"x_unit_lb={x_unit_lb},n_forward={n_forward})"
            ),
            **kwargs,
        )

    def _transform_output(self, output):
        trigger, change, trigger_location = output
        return trigger, change, trigger_location
