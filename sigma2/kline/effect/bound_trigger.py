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
        upper: float,
        lower: float,
        horizon: int,
        *,
        unit_field: str = "close",
        **kwargs: Any,
    ) -> None:
        self.upper = upper
        self.lower = lower
        self.horizon = horizon
        self.unit_field = unit_field
        super().__init__(
            rBoundTrigger,
            effect_args=(upper, lower, horizon),
            inputs=(unit_field, "open", "high", "low", "close"),
            schema={
                "trigger": Scalar(low=-1, high=1, dtype="int8"),
                "unit_change": Scalar(low=-float("inf"), high=float("inf"), dtype="float64"),
                "trigger_index": Scalar(low=-1, high=np.iinfo(np.int64).max, dtype="int64"),
            },
            output_transform=self._transform_output,
            full_name=f"{self.name}(unit={unit_field},upper={upper},lower={lower},horizon={horizon})",
            **kwargs,
        )

    def _transform_output(self, output):
        trigger, change, trigger_location = output
        return trigger, change, trigger_location
