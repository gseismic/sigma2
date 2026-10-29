from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.kline.outcome_base import rKlineOutcome

_FIELDS = frozenset({"open", "high", "low", "close", "volume"})


class rKlineFutureReturn(rKlineOutcome):
    """计算锚点到未来末端的收益，要求完整未来区间有效。"""

    name = "kline_future_return"

    def __init__(
        self,
        n_forward: int,
        *,
        field: str = "close",
        return_type: str = "simple",
        buffer_size: int = 1,
    ) -> None:
        if not isinstance(return_type, str) or return_type.lower() not in {
            "simple",
            "log",
        }:
            raise ValueError("return_type must be 'simple' or 'log'")
        if not isinstance(field, str) or field not in _FIELDS:
            raise ValueError(f"unsupported K-line field: {field!r}")
        self._return_type = return_type.lower()
        self._field = field
        self._output_key = "log_return" if self.return_type == "log" else "return"
        super().__init__(
            schema={
                self._output_key: Scalar(low=-np.inf, high=np.inf, dtype=np.float64)
            },
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
            return {self._output_key: float("nan")}
        window = np.asarray(values, dtype=float)
        if not np.all(np.isfinite(window)) or window[0] == 0:
            return {self._output_key: float("nan")}
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            ratio = window[-1] / window[0]
            if self.return_type == "log":
                result = np.log(ratio) if ratio > 0 else np.nan
            else:
                result = ratio - 1.0
        return {
            self._output_key: float(result) if np.isfinite(result) else float("nan")
        }

    @property
    def field(self) -> str:
        return self._field

    @property
    def return_type(self) -> str:
        return self._return_type

    @property
    def full_name(self) -> str:
        return (
            f"{self.name}({self.field},{self.n_forward},return_type={self.return_type})"
        )


__all__ = ["rKlineFutureReturn"]
