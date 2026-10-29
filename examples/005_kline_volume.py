"""量价指标：计算 OBV、MFI 和滚动 VWAP。"""

from sigma2 import KlineMFI, KlineOBV, KlineVWAP


def main() -> None:
    bars = [
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": volume,
            "open_time": i,
        }
        for i, (close, volume) in enumerate(
            [(10, 100), (11, 120), (13, 110), (12, 130), (14, 140), (15, 150)]
        )
    ]
    print("OBV：", KlineOBV(bars)["obv"])
    print("MFI：", KlineMFI(bars, 3)["mfi"])
    print("VWAP：", KlineVWAP(bars, 3)["vwap"])


if __name__ == "__main__":
    main()
