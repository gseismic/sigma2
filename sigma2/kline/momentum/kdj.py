from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply, rKlineWindowSignal


class rKlineKDJ(rKlineWindowSignal):
    """按 symbol 计算 KDJ；缺失窗口后重新初始化递推状态。"""

    name = "KDJ"

    def __init__(self, n1: int = 9, n2: int = 3, n3: int = 3, **kwargs: Any) -> None:
        self.n1 = ensure_integer(n1, "n1", min_value=1)
        self.n2 = ensure_integer(n2, "n2", min_value=1)
        self.n3 = ensure_integer(n3, "n3", min_value=1)
        if self.n1 <= self.n2 or self.n1 <= self.n3:
            raise ValueError("n1 must be greater than n2 and n3")
        super().__init__(
            schema={
                key: Scalar(low=-np.inf, high=np.inf, dtype=np.float64)
                for key in ("k", "d", "j")
            },
            n_backward=self.n1 - 1,
            history_window=self.n1,
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        self._k = 50.0
        self._d = 50.0

    def forward(self, opens, highs, lows, closes, volumes):
        if len(closes) < self.n1:
            return np.nan, np.nan, np.nan
        if not (
            np.all(np.isfinite(highs))
            and np.all(np.isfinite(lows))
            and np.isfinite(closes[-1])
        ):
            self._k = self._d = 50.0
            return np.nan, np.nan, np.nan
        high, low = np.max(highs), np.min(lows)
        rsv = 50.0 if high == low else (closes[-1] - low) / (high - low) * 100.0
        k = (self._k * (self.n2 - 1) + rsv) / self.n2
        d = (self._d * (self.n3 - 1) + k) / self.n3
        self._k, self._d = k, d
        return k, d, 3 * k - 2 * d

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.n1},{self.n2},{self.n3})[high,low,close]"


def KlineKDJ(
    data: Any,
    n1: int = 9,
    n2: int = 3,
    n3: int = 3,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbol: str | None = None,
    key_map: Mapping[str, str] | None = None,
) -> Any:
    """逐时点重放 KDJ。"""
    return forward_signal_apply(
        data,
        rKlineKDJ,
        param_args=(n1, n2, n3),
        return_type=return_type,
        return_meta_info=return_meta_info,
        symbol=symbol,
        key_map=key_map,
    )


__all__ = ["KlineKDJ", "rKlineKDJ"]
