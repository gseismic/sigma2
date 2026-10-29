from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.batch import forward_signal_apply
from sigma2.kline.window import rKlineWindowSignal


class rKlineReturn(rKlineWindowSignal):
    """基于 close 的 n 根 K 线收益率。"""

    name = "return"

    def __init__(self, n: int = 1, **kwargs: Any) -> None:
        self.n = ensure_integer(n, "n", min_value=1)
        super().__init__(
            schema=[("return", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            n_backward=self.n,
            history_window=self.n + 1,
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes) -> float:
        if len(closes) <= self.n:
            return float("nan")
        previous = closes[-self.n - 1]
        current = closes[-1]
        if not (np.isfinite(previous) and np.isfinite(current)) or previous == 0:
            return float("nan")
        with np.errstate(over="ignore", invalid="ignore"):
            output = current / previous - 1.0
        return float(output) if np.isfinite(output) else float("nan")

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.n})"


def KlineReturn(
    data: Any,
    n: int = 1,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbol: str | None = None,
    key_map: Mapping[str, str] | None = None,
) -> Any:
    """批量 replay :class:`rKlineReturn`。"""

    return forward_signal_apply(
        data,
        rKlineReturn,
        param_args=(n,),
        return_type=return_type,
        return_meta_info=return_meta_info,
        symbol=symbol,
        key_map=key_map,
    )


__all__ = ["KlineReturn", "rKlineReturn"]
