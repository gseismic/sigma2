from __future__ import annotations

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.families import rOrderBookSignal


class rBookSpread(rOrderBookSignal):
    """订单簿快照的最优卖价减最优买价。"""

    name = "book_spread"

    def __init__(self, **kwargs) -> None:
        super().__init__(
            window=1,
            schema=[("spread", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            **kwargs,
        )

    def reset_extras(self) -> None:
        pass

    def forward(self, bids, asks) -> float:
        if not bids or not asks:
            return float("nan")
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        return float(best_ask - best_bid)

    @property
    def full_name(self) -> str:
        return str(self.name)
