"""K 线截面：计算每个 symbol 的 lag 步收益率排名。"""

from sigma2 import KlineBundleReturnRank, rKlineBundleReturnRank


def main() -> None:
    snapshots = [
        {
            "open_time": 0,
            "bundle": {
                "BTC": {"open": 100, "high": 101, "low": 99, "close": 100},
                "ETH": {"open": 200, "high": 201, "low": 199, "close": 200},
                "SOL": {"open": 100, "high": 101, "low": 99, "close": 100},
            },
        },
        {
            "open_time": 1,
            # BTC 和 ETH 收益率相同，按本次输入顺序依次排名。
            "bundle": {
                "BTC": {"open": 110, "high": 111, "low": 109, "close": 110},
                "ETH": {"open": 220, "high": 221, "low": 219, "close": 220},
                "SOL": {"open": 100, "high": 101, "low": 99, "close": 100},
            },
        },
        {
            "open_time": 2,
            "has_missing": True,
            "bundle": {
                "BTC": {"open": 120, "high": 121, "low": 119, "close": 120},
                "ETH": {"open": 220, "high": 221, "low": 219, "close": None},
                "SOL": {
                    "open": float("nan"),
                    "high": float("nan"),
                    "low": float("nan"),
                    "close": float("nan"),
                    "is_missing": True,
                },
                "DOGE": {"open": 10, "high": 11, "low": 9, "close": 10},
            },
        },
        {
            "open_time": 3,
            "bundle": {
                "BTC": {"open": 130, "high": 131, "low": 129, "close": 130},
                "ETH": {"open": 230, "high": 231, "low": 229, "close": 230},
                "SOL": {"open": 90, "high": 91, "low": 89, "close": 90},
                "DOGE": {"open": 12, "high": 13, "low": 11, "close": 12},
            },
        },
    ]
    rank = rKlineBundleReturnRank(lag=1)
    for snapshot in snapshots:
        print("每个 symbol 的收益率排名：", rank.step(**snapshot)["rank"])
    print("使用字段：", rank.meta_info["used_fields"])

    columns = KlineBundleReturnRank(snapshots, lag=1)
    print("逐时点排名：", columns["rank"])


if __name__ == "__main__":
    main()
