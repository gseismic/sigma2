"""逐笔成交：根据方向计算带符号的成交量。"""

from sigma2 import forward_step_apply, rTradeSignedVolume


def main() -> None:
    trades = [
        {"price": 100.5, "volume": 3.0, "side": "buy"},
        {"price": 100.4, "volume": 2.0, "side": "sell"},
        {"price": 100.4, "volume": 4.0, "side": None},
    ]
    signal = rTradeSignedVolume()
    for trade in trades:
        print("有向成交量：", signal.step(**trade))
    print("使用字段：", signal.meta_info["used_fields"])
    print(
        "批量结果：", forward_step_apply(trades, rTradeSignedVolume())["signed_volume"]
    )


if __name__ == "__main__":
    main()
