from __future__ import annotations

from typing import Any

import numpy as np
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply, rKlineWindowSignal


class rKlineReturn(rKlineWindowSignal):
    """基于 close 的 n 根 K 线收益率。"""

    name = "return"

    def __init__(self, n: int = 1, **kwargs: Any) -> None:
        self.n = ensure_integer(n, "n", min_value=1)
        super().__init__(
            window=self.n + 1,
            schema=[("return", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes) -> float:
        if len(closes) <= self.n:
            return float("nan")
        previous = closes[-self.n - 1]
        if previous == 0:
            return float("nan")
        return float(closes[-1] / previous - 1.0)

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.n})"


def KlineReturn(
    data: Any,
    n: int = 1,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """批量 replay :class:`rKlineReturn`。"""

    return forward_signal_apply(
        data,
        rKlineReturn,
        param_args=(n,),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineReturn", "rKlineReturn"]
