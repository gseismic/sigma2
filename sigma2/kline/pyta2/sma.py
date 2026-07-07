from __future__ import annotations

from typing import Any

from sigma2.core import rPyta2Signal


class rPyta2SMA(rPyta2Signal):
    """pyta2 rSMA 的类式快捷适配。"""

    name = "pyta2_sma"

    def __init__(self, n: int, *, field: str = "close", **kwargs: Any) -> None:
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
