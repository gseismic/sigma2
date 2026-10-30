"""K 线截面：固定权重和动态市值权重的价格指数。"""

from sigma2 import (
    KlineBundleFixedWeightIndex,
    KlineBundleMarketCapWeightedIndex,
    rKlineBundleFixedWeightIndex,
    rKlineBundleMarketCapWeightedIndex,
)


def main() -> None:
    snapshots = [
        {
            "open_time": 0,
            "bundle": {
                "BTC": {
                    "open": 100,
                    "high": 101,
                    "low": 99,
                    "close": 100,
                    "market_cap": 300,
                },
                "ETH": {
                    "open": 200,
                    "high": 201,
                    "low": 199,
                    "close": 200,
                    "market_cap": 100,
                },
            },
        },
        {
            "open_time": 1,
            "bundle": {
                "BTC": {
                    "open": 110,
                    "high": 111,
                    "low": 109,
                    "close": 110,
                    "market_cap": 100,
                },
                "ETH": {
                    "open": 210,
                    "high": 211,
                    "low": 209,
                    "close": 210,
                    "market_cap": 300,
                },
            },
        },
    ]
    # SOL 不在固定权重中，缺失它只影响市值加权的结果。
    snapshots.append(
        {
            "open_time": 2,
            "has_missing": True,
            "bundle": {
                **snapshots[-1]["bundle"],
                "SOL": {
                    "open": None,
                    "high": None,
                    "low": None,
                    "close": None,
                    "market_cap": None,
                    "is_missing": True,
                },
            },
        }
    )

    fixed = rKlineBundleFixedWeightIndex({"BTC": 1, "ETH": 1})
    market_cap = rKlineBundleMarketCapWeightedIndex()
    for snapshot in snapshots:
        print("固定权重：", fixed.step(**snapshot))
        print("动态市值：", market_cap.step(**snapshot))
    print("市值加权使用字段：", market_cap.meta_info["used_fields"])
    print(
        "批量固定权重：", KlineBundleFixedWeightIndex(snapshots, {"BTC": 1, "ETH": 1})
    )
    print("批量动态市值：", KlineBundleMarketCapWeightedIndex(snapshots))


if __name__ == "__main__":
    main()
