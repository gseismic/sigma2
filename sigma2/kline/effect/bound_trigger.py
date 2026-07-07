from __future__ import annotations

from typing import Any

from pyta2.effect import rBoundTrigger

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
            full_name=f"{self.name}(unit={unit_field},upper={upper},lower={lower},horizon={horizon})",
            **kwargs,
        )
