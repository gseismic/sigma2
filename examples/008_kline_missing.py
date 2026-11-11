"""缺失数据：成交量缺省和整根 K 线缺失均会推进时间。"""

from sigma2 import rKlineMA


def main() -> None:
    ma = rKlineMA(2, field="volume")
    missing = float("nan")
    bars = [
        {"open": 10, "high": 10, "low": 10, "close": 10, "volume": 100, "open_time": 0},
        {"open": 11, "high": 11, "low": 11, "close": 11, "open_time": 1},
        {
            "open": missing,
            "high": missing,
            "low": missing,
            "close": missing,
            "volume": missing,
            "open_time": 2,
            "is_missing": True,
        },
        {"open": 12, "high": 12, "low": 12, "close": 12, "volume": 200, "open_time": 3},
        {"open": 13, "high": 13, "low": 13, "close": 13, "volume": 300, "open_time": 4},
    ]
    for bar in bars:
        print("观测索引：", ma.g_index + 1, "均线：", ma.step(**bar))


if __name__ == "__main__":
    main()
