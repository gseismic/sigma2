"""均线：逐条计算已确定的 K 线，以及批量重放。"""

from sigma2 import KlineMA, rKlineMA


def main() -> None:
    bars = [
        {"open": 10, "high": 10, "low": 10, "close": 10, "open_time": 0},
        {"open": 20, "high": 20, "low": 20, "close": 20, "open_time": 1},
        {
            "open": 30,
            "high": 40,
            "low": 30,
            "close": 40,
            "open_time": 2,
        },
    ]

    ma = rKlineMA(2, ma_type="SMA")
    for bar in bars:
        print("逐条均线：", ma.step(**bar), "观测索引：", ma.g_index)
    print("使用字段：", ma.meta_info["used_fields"])

    columns = KlineMA(bars, 2, ma_type="SMA")
    print("批量均线：", columns["ma"])


if __name__ == "__main__":
    main()
