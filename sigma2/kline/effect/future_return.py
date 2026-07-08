from __future__ import annotations

from typing import Any

import numpy as np
from pyta2.effect import rFutureReturn
from pyta2.utils.space import Scalar

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
        return_type = return_type.lower()
        if return_type not in {"simple", "log"}:
            raise ValueError(f"return_type must be 'simple' or 'log', got {return_type!r}")
        self.horizon = horizon
        self.field = field
        self.return_type = return_type
        output_key = "log_return" if return_type == "log" else "return"
        super().__init__(
            rFutureReturn,
            effect_args=(horizon,),
            inputs=(field,),
            schema={output_key: Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            output_transform=self._transform_return,
            full_name=f"{self.name}({field},{horizon},return_type={return_type})",
            **kwargs,
        )

    def _transform_return(self, pct_change):
        if self.return_type == "simple":
            return pct_change
        if pct_change <= -1 or not np.isfinite(pct_change):
            return np.nan
        return np.log1p(pct_change)
