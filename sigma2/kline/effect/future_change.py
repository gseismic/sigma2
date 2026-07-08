from __future__ import annotations

from typing import Any

from pyta2.effect import rFutureChange

from .base import rKlineEffectSignal


class rKlineFutureChange(rKlineEffectSignal):
    """K 线字段的未来绝对变动 target。"""

    name = "kline_future_change"

    def __init__(self, horizon: int, *, field: str = "close", **kwargs: Any) -> None:
        self.horizon = horizon
        self.field = field
        super().__init__(
            rFutureChange,
            effect_args=(horizon,),
            inputs=(field,),
            full_name=f"{self.name}({field},{horizon})",
            _trusted_stateless=True,
            **kwargs,
        )
