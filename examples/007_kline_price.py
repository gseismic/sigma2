"""价格变化：计算收盘价收益率和相对前收盘价的跳空。"""

from sigma2 import KlineGap, KlineReturn


def main() -> None:
    bars = [
        {"open": 10, "high": 11, "low": 9, "close": 10, "open_time": 0},
        {"open": 11, "high": 12, "low": 10, "close": 12, "open_time": 1},
        {"open": 13, "high": 14, "low": 12, "close": 13, "open_time": 2},
    ]
    print("跳空：", KlineGap(bars)["gap"])
    print("两步收益率：", KlineReturn(bars, lag=2)["return"])


if __name__ == "__main__":
    main()
