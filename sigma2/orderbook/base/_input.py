from __future__ import annotations

from collections.abc import Sequence
from typing import Any

BookLevel = tuple[float, float]


class _OrderBookStep:
    """单 symbol 盘口快照的输入入口。"""

    family = "orderbook"
    input_schema_details = {
        name: {
            "type": "sequence",
            "items": {
                "type": "tuple",
                "items": [{"type": "number"}, {"type": "number"}],
            },
        }
        for name in ("bids", "asks")
    }

    def step(
        self, *, bids: Sequence[BookLevel], asks: Sequence[BookLevel]
    ) -> dict[str, Any]:
        return super().step(bids=bids, asks=asks)
