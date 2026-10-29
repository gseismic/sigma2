"""波动指标：计算 ATR 和布林带。"""

from sigma2 import KlineATR, KlineBoll


def main() -> None:
    bars = [
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "open_time": i,
        }
        for i, close in enumerate([10, 11, 13, 12, 14, 15])
    ]
    atr, info = KlineATR(bars, 3, ma_type="EMA", return_meta_info=True)
    boll = KlineBoll(bars, 3, F=2)
    print("ATR：", atr["atr"], "使用字段：", info["used_fields"])
    print("布林带上、中、下轨：", boll)


if __name__ == "__main__":
    main()
