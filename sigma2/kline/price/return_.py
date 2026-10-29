from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.core.utils import forward_step_apply
from sigma2.kline.signal import rKlineSignal


class rKlineReturn(rKlineSignal):
    """基于 close 的 n 根 K 线收益率。"""

    name = "return"

    def __init__(self, n: int = 1, *, buffer_size: int = 1) -> None:
        self._n = ensure_integer(n, "n", min_value=1)
        super().__init__(
            schema={"return": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            n_backward=self.n,
            buffer_size=buffer_size,
            used_fields=("close",),
        )
        self._state["closes"] = deque(maxlen=self.n + 1)

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
    ) -> dict[str, float]:
        closes = self._state["closes"]
        closes.append(close)
        if len(closes) <= self.n:
            return {"return": float("nan")}
        previous = closes[0]
        if not (np.isfinite(previous) and np.isfinite(close)) or previous == 0:
            return {"return": float("nan")}
        with np.errstate(over="ignore", invalid="ignore"):
            result = close / previous - 1.0
        return {"return": float(result) if np.isfinite(result) else float("nan")}

    @property
    def n(self) -> int:
        return self._n

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.n})"


def KlineReturn(
    data: Iterable[Mapping[str, Any]],
    n: int = 1,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """逐条重放 K 线并输出收益率。"""
    return forward_step_apply(
        data,
        rKlineReturn(n, buffer_size=0),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineReturn", "rKlineReturn"]
