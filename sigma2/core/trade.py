from __future__ import annotations

from abc import abstractmethod
from typing import Any, Literal

from .signal import rSignal

TradeSide = Literal["buy", "sell"] | None


class rTradeSignal(rSignal):
    """实验性的逐笔成交事件 signal family。"""

    family = "trade"
    step_input_keys = ("price", "volume", "side")

    def step(self, *, price: float, volume: float, side: TradeSide = None) -> Any:
        return super().step(price, volume, side)

    @abstractmethod
    def forward(self, price: float, volume: float, side: TradeSide = None) -> Any:
        raise NotImplementedError
