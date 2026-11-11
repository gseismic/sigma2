from __future__ import annotations

from collections.abc import Sequence
from typing import Any

BookLevel = tuple[float, float]


class _OrderBookStep:
    """单 symbol 盘口快照的输入入口。"""

    family = "orderbook"
    input_schema_details = [
        {
            "name": name,
            "type": "sequence",
            "description": "盘口档位序列",
            "items": {
                "type": "tuple",
                "description": "价格与数量的二元组，两个值均为数值",
            },
        }
        for name in ("bids", "asks")
    ]

    def step(
        self, *, bids: Sequence[BookLevel], asks: Sequence[BookLevel]
    ) -> dict[str, Any]:
        return super().step(bids=bids, asks=asks)
