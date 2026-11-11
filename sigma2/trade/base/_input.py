from __future__ import annotations

from typing import Any, Literal

TradeSide = Literal["buy", "sell"] | None


class _TradeStep:
    """单 symbol 成交事件的输入入口。"""

    family = "trade"
    input_schema_details = [
        {"name": "price", "type": "number"},
        {"name": "volume", "type": "number"},
        {"name": "side", "type": "string", "description": "buy、sell 或 None"},
    ]

    def step(
        self, *, price: float, volume: float, side: TradeSide = None
    ) -> dict[str, Any]:
        return super().step(price=price, volume=volume, side=side)
