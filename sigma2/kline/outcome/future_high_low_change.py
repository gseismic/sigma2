from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.kline.outcome_base import rKlineOutcome

_FIELDS = frozenset({"open", "high", "low", "close", "volume"})


class rKlineFutureHighLowChange(rKlineOutcome):
    """计算未来窗口的最高价和最低价相对锚点的变化。"""

    name = "kline_future_high_low_change"

    def __init__(
        self,
        n_forward: int,
        *,
        reference_field: str = "close",
        buffer_size: int = 1,
    ) -> None:
        if not isinstance(reference_field, str) or reference_field not in _FIELDS:
            raise ValueError(f"unsupported K-line field: {reference_field!r}")
        self._reference_field = reference_field
        super().__init__(
            schema={
                key: Scalar(low=-np.inf, high=np.inf, dtype=np.float64)
                for key in ("high_change", "low_change")
            },
            n_forward=n_forward,
            buffer_size=buffer_size,
            used_fields=tuple(dict.fromkeys(("high", "low", reference_field))),
        )
        self._values = deque(maxlen=self.n_forward + 1)

    def forward(
        self,
        open,
        high,
        low,
        close,
        volume=None,
        *,
        open_time=None,
        is_missing=False,
    ) -> dict[str, Any]:
        fields = {
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
        reference = fields[self.reference_field]
        values = self._values
        values.append((high, low, float("nan") if reference is None else reference))
        result = {"high_change": float("nan"), "low_change": float("nan")}
        if len(values) <= self.n_forward:
            return result
        history = np.asarray(values, dtype=float)
        anchor = history[0, 2]
        if not np.isfinite(anchor):
            return result
        for key, future, extreme in (
            ("high_change", history[1:, 0], np.max),
            ("low_change", history[1:, 1], np.min),
        ):
            if np.all(np.isfinite(future)):
                with np.errstate(over="ignore", invalid="ignore"):
                    value = extreme(future) - anchor
                result[key] = float(value) if np.isfinite(value) else float("nan")
        return result

    @property
    def reference_field(self) -> str:
        return self._reference_field

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.reference_field},{self.n_forward})"


__all__ = ["rKlineFutureHighLowChange"]
