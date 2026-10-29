from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.kline.outcome_base import rKlineOutcome

_FIELDS = frozenset({"open", "high", "low", "close", "volume"})


class rKlineFutureChange(rKlineOutcome):
    """计算锚点到未来末端的绝对变化，要求完整未来区间有效。"""

    name = "kline_future_change"

    def __init__(
        self, n_forward: int, *, field: str = "close", buffer_size: int = 1
    ) -> None:
        if not isinstance(field, str) or field not in _FIELDS:
            raise ValueError(f"unsupported K-line field: {field!r}")
        self._field = field
        super().__init__(
            schema={"value": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            n_forward=n_forward,
            buffer_size=buffer_size,
            used_fields=(field,),
        )
        self._state["values"] = deque(maxlen=self.n_forward + 1)

    def forward(
        self,
        open,
        high,
        low,
        close,
        volume=None,
        *,
        open_time=None,
        is_closed=True,
        is_missing=False,
    ) -> dict[str, Any]:
        value = {
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }[self.field]
        values = self._state["values"]
        values.append(float("nan") if value is None else value)
        if len(values) <= self.n_forward:
            return {"value": float("nan")}
        window = np.asarray(values, dtype=float)
        if not np.all(np.isfinite(window)):
            return {"value": float("nan")}
        with np.errstate(over="ignore", invalid="ignore"):
            result = window[-1] - window[0]
        return {"value": float(result) if np.isfinite(result) else float("nan")}

    @property
    def field(self) -> str:
        return self._field

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.field},{self.n_forward})"


__all__ = ["rKlineFutureChange"]
