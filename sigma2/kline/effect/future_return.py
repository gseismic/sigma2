from __future__ import annotations

from typing import Any

from pyta2.effect import rFutureReturn

from .base import rKlineEffectSignal


class rKlineFutureReturn(rKlineEffectSignal):
    """K 线字段的未来收益 target。"""

    name = "kline_future_return"

    def __init__(
        self,
        horizon: int,
        *,
        field: str = "close",
        return_type: str = "simple",
        **kwargs: Any,
    ) -> None:
        self.horizon = horizon
        self.field = field
        self.return_type = return_type
        super().__init__(
            rFutureReturn,
            effect_args=(horizon,),
            effect_kwargs={"return_type": return_type},
            inputs=(field,),
            full_name=f"{self.name}({field},{horizon},return_type={return_type})",
            **kwargs,
        )
