from __future__ import annotations

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.orderbook.signal import rOrderBookSignal


class rBookSpread(rOrderBookSignal):
    """订单簿快照的最优卖价减最优买价。"""

    name = "book_spread"

    def __init__(self, *, buffer_size: int = 1) -> None:
        super().__init__(
            schema={"spread": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            buffer_size=buffer_size,
            used_fields=("bids", "asks"),
        )

    def forward(self, bids, asks) -> dict[str, float]:
        if not bids or not asks:
            return {"spread": float("nan")}
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        return {"spread": float(best_ask - best_bid)}

    @property
    def full_name(self) -> str:
        return str(self.name)
