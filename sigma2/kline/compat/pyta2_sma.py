from __future__ import annotations

from typing import Any

from sigma2.core import rPyta2Signal

from ._warnings import warn_deprecated


class rPyta2SMA(rPyta2Signal):
    """兼容旧桥接快捷类；新代码使用 ``rKlineMA(ma_type='SMA')``。"""

    name = "pyta2_sma"

    def __init__(self, n: int, *, field: str = "close", **kwargs: Any) -> None:
        warn_deprecated("rPyta2SMA", "rKlineMA(..., ma_type='SMA')")
        if n <= 0:
            raise ValueError(f"n must be greater than 0, got {n}")
        self.n = n
        self.field = field
        super().__init__(
            "SMA",
            params={"n": n},
            field=field,
            **kwargs,
        )


__all__ = ["rPyta2SMA"]
