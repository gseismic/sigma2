from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sigma2.core.signal import rSignal

BookLevel = tuple[float, float]


class rOrderBookSignal(rSignal):
    """逐个处理订单簿快照。"""

    family = "orderbook"

    def step(
        self, *, bids: Sequence[BookLevel], asks: Sequence[BookLevel]
    ) -> dict[str, Any]:
        return self._step({"bids": bids, "asks": asks})


__all__ = ["BookLevel", "rOrderBookSignal"]
