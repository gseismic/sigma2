"""自定义有状态成交 Signal，演示状态保存、重置和批量重放。"""

from sigma2 import forward_step_apply, rTradeSignal


class rTradeCumulativeSignedVolume(rTradeSignal):
    """当前输入流中买量减卖量的累计值。"""

    name = "trade_cumulative_signed_volume"

    def forward(self, price: float, volume: float, side: str | None = None) -> dict:
        total = self._state.get("total", 0.0)
        if side == "buy":
            total += volume
        elif side == "sell":
            total -= volume
        elif side is not None:
            raise ValueError(f"unknown trade side: {side!r}")
        self._state["total"] = total
        return {"total": total}


def main() -> None:
    signal = rTradeCumulativeSignedVolume(used_fields=("volume", "side"))
    signal.step(price=100.0, volume=3.0, side="buy")
    signal.step(price=101.0, volume=2.0, side="sell")
    print("下一笔成交：", signal.step(price=101.0, volume=4.0, side="sell"))
    print("累计值与索引：", signal.outputs["total"][-1], signal.g_index)
    signal.reset()
    print("重置后的索引：", signal.g_index)

    finalized = [
        {"price": 100.0, "volume": 3.0, "side": "buy"},
        {"price": 101.0, "volume": 2.0, "side": "sell"},
        {"price": 101.0, "volume": 4.0, "side": "sell"},
    ]
    batch = forward_step_apply(finalized, rTradeCumulativeSignedVolume())
    print("批量重放：", batch["total"])


if __name__ == "__main__":
    main()
