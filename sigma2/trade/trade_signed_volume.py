from __future__ import annotations

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.trade.signal import rTradeSignal


class rTradeSignedVolume(rTradeSignal):
    """带方向成交量：buy 为正，sell 为负，未知方向为 0。"""

    name = "trade_signed_volume"

    def __init__(self, *, buffer_size: int = 1) -> None:
        super().__init__(
            schema={
                "signed_volume": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)
            },
            buffer_size=buffer_size,
            used_fields=("volume", "side"),
        )

    def forward(self, price, volume, side=None) -> dict[str, float]:
        if side == "buy":
            return {"signed_volume": float(volume)}
        if side == "sell":
            return {"signed_volume": float(-volume)}
        if side is None:
            return {"signed_volume": 0.0}
        raise ValueError(f"side must be 'buy', 'sell' or None, got {side!r}")

    @property
    def full_name(self) -> str:
        return str(self.name)
