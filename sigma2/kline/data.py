from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np

from sigma2.core._kline_data import utc_time


@dataclass(frozen=True, slots=True)
class KlineBar:
    """单 symbol 已确认 K 线；显式占位用于推进缺失的共同时间。"""

    symbol: str
    bar_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    available_at: datetime | None = None
    is_missing: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("symbol must be a non-empty string")
        object.__setattr__(self, "bar_time", utc_time(self.bar_time, "bar_time"))
        if self.available_at is not None:
            object.__setattr__(
                self, "available_at", utc_time(self.available_at, "available_at")
            )
        for field in ("open", "high", "low", "close", "volume"):
            object.__setattr__(self, field, float(getattr(self, field)))
        if not isinstance(self.is_missing, bool):
            raise TypeError("is_missing must be bool")
        if self.is_missing and not all(
            np.isnan(getattr(self, field))
            for field in ("open", "high", "low", "close", "volume")
        ):
            raise ValueError("a missing bar must have NaN values for all OHLCV fields")


__all__ = ["KlineBar"]
