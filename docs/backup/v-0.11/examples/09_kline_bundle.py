"""多 symbol 排名与未来收益：在 examples 目录运行 python 09_kline_bundle.py。"""

from sigma2.kline_bundle import (
    KlineBundleFutureReturn,
    rKlineBundleFutureReturn,
    rKlineBundleMA,
    rKlineBundleRank,
)


def main() -> None:
    symbols = ("A", "B")
    bundles = [
        {
            "open_time": index,
            "available_at": index + 1,
            "bundle": {
                symbol: {"open": price, "high": price, "low": price, "close": price}
                for symbol, price in prices.items()
            },
        }
        for index, prices in enumerate(
            [{"A": 100, "B": 200}, {"A": 110}, {"A": 121, "B": 242}]
        )
    ]
    rank = rKlineBundleRank(symbols=symbols, return_dict=True)
    ma = rKlineBundleMA(2, symbols=symbols, return_dict=True)
    outcome = rKlineBundleFutureReturn(1, symbols=symbols, return_dict=True)
    for bundle in bundles:
        print("时点：", bundle["open_time"], "存在：", tuple(bundle["bundle"]))
        print("排名：", rank.step(bundle), "均线：", ma.step(bundle))
        value = outcome.step(bundle)
        if outcome.result_index >= 0:
            print("未来收益所属锚点：", outcome.result_index, value)
    values, metadata = KlineBundleFutureReturn(
        bundles, 1, symbols=symbols, return_meta_info=True
    )
    print("symbol 轴：", metadata["symbols"])
    print("按锚点回填：", values)
    print("输入最早齐备时间：", metadata["result_input_ready_at"])


if __name__ == "__main__":
    main()
