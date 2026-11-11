from __future__ import annotations

from collections.abc import Sequence
from typing import Any

BookLevel = tuple[float, float]


class _OrderBookStep:
    """单 symbol 盘口快照的输入入口。"""

    family = "orderbook"

    def step(
        self, *, bids: Sequence[BookLevel], asks: Sequence[BookLevel]
    ) -> dict[str, Any]:
        return super().step(bids=bids, asks=asks)
