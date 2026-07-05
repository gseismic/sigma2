from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from sigma2.base import rSignal

BookLevel = tuple[float, float]


class rOrderBookSignal(rSignal):
    """实验性的订单簿快照 signal family。"""

    family = "orderbook"
    step_input_keys = ("bids", "asks")

    def step(self, *, bids: Sequence[BookLevel], asks: Sequence[BookLevel]) -> Any:
        return super().step(bids, asks)

    @abstractmethod
    def forward(self, bids: Sequence[BookLevel], asks: Sequence[BookLevel]) -> Any:
        raise NotImplementedError
