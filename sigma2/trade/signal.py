from __future__ import annotations

from typing import Any, Literal

from sigma2.core.signal import rSignal

TradeSide = Literal["buy", "sell"] | None


class rTradeSignal(rSignal):
    """逐个处理成交事件。"""

    family = "trade"

    def step(
        self, *, price: float, volume: float, side: TradeSide = None
    ) -> dict[str, Any]:
        return super().step(price=price, volume=volume, side=side)


__all__ = ["TradeSide", "rTradeSignal"]
