from __future__ import annotations

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.families import rTradeSignal


class rTradeSignedVolume(rTradeSignal):
    """带方向成交量：buy 为正，sell 为负，未知方向为 0。"""

    name = "trade_signed_volume"

    def __init__(self, **kwargs) -> None:
        super().__init__(
            window=1,
            schema=[
                ("signed_volume", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))
            ],
            **kwargs,
        )

    def reset_extras(self) -> None:
        pass

    def forward(self, price, volume, side=None) -> float:
        if side == "buy":
            return float(volume)
        if side == "sell":
            return float(-volume)
        if side is None:
            return 0.0
        raise ValueError(f"side must be 'buy', 'sell' or None, got {side!r}")

    @property
    def full_name(self) -> str:
        return str(self.name)
