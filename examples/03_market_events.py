"""盘口快照与逐笔成交的独立输入：运行 python -m examples.03_market_events。"""

from sigma2 import rBookSpread, rTradeSignedVolume


def main() -> None:
    spread = rBookSpread(return_dict=True)
    print(
        "首个盘口：",
        spread.step(
            bids=[(100.0, 2.0), (99.5, 3.0)],
            asks=[(100.75, 1.0), (101.0, 4.0)],
        ),
    )
    print(
        "修订盘口：",
        spread.update_last(
            bids=[(100.25, 2.0), (99.5, 3.0)],
            asks=[(100.75, 1.0), (101.0, 4.0)],
        ),
    )

    signed_volume = rTradeSignedVolume(return_dict=True)
    print("买单：", signed_volume.step(price=100.5, volume=3.0, side="buy"))
    print("卖单：", signed_volume.step(price=100.4, volume=2.0, side="sell"))
    print(
        "修订最后成交：",
        signed_volume.update_last(price=100.4, volume=4.0, side="sell"),
    )


if __name__ == "__main__":
    main()
