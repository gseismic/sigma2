"""动量指标：同一组 K 线分别计算 RSI 和 KDJ。"""

from sigma2 import KlineKDJ, KlineRSI


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
    rsi = KlineRSI(bars, 3)
    kdj = KlineKDJ(bars, 3, 2, 2)
    print("RSI：", rsi["rsi"])
    print("K、D、J：", kdj)


if __name__ == "__main__":
    main()
