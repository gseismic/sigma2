"""自定义有状态成交 Signal：运行 python -m examples.06_custom_signal。"""

import numpy as np
from pyta2.utils.space import Scalar

from sigma2 import forward_signal_apply, rTradeSignal


class rTradeCumulativeSignedVolume(rTradeSignal):
    """当前输入流中买量减卖量的累计值。"""

    name = "trade_cumulative_signed_volume"
    _update_state_fields = ("_total",)

    def __init__(self, **kwargs) -> None:
        super().__init__(
            window=1,
            schema={"total": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            **kwargs,
        )

    def reset_extras(self) -> None:
        self._total = 0.0

    def forward(self, price: float, volume: float, side: str | None = None) -> float:
        if side == "buy":
            self._total += volume
        elif side == "sell":
            self._total -= volume
        elif side is not None:
            raise ValueError(f"unknown trade side: {side!r}")
        return self._total

    @property
    def full_name(self) -> str:
        return str(self.name)


def main() -> None:
    signal = rTradeCumulativeSignedVolume()
    signal.step(price=100.0, volume=3.0, side="buy")
    signal.step(price=101.0, volume=2.0, side="sell")
    print("修订最后成交：", signal.update_last(price=101.0, volume=4.0, side="sell"))
    print("累计值与索引：", signal.latest, signal.g_index)

    finalized = {
        "price": [100.0, 101.0],
        "volume": [3.0, 4.0],
        "side": ["buy", "sell"],
    }
    batch = forward_signal_apply(finalized, rTradeCumulativeSignedVolume)
    print("批量重放：", batch[signal.factor_names[0]])


if __name__ == "__main__":
    main()
