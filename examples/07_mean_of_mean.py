"""不调用 pyta2 指标的两级均值 Signal：运行 python -m examples.07_mean_of_mean。"""

from sigma2.kline import KlineMeanOfMean, rKlineMeanOfMean


def _bar(close: float) -> dict[str, float]:
    return {
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": 1.0,
    }


def main() -> None:
    signal = rKlineMeanOfMean(inner_n=2, outer_n=2, return_dict=True)
    for close in (1.0, 2.0, 3.0):
        print("新 K 线：", close, signal.step(**_bar(close)))

    print("修订末根：", signal.update_last(**_bar(5.0)))
    print("继续推进：", signal.step(**_bar(4.0)))
    print("列名：", signal.factor_names)

    closes = [1.0, 2.0, 5.0, 4.0]
    data = {key: closes for key in ("open", "high", "low", "close")}
    data["volume"] = [1.0] * len(closes)
    print("批量重放：", KlineMeanOfMean(data, inner_n=2, outer_n=2))


if __name__ == "__main__":
    main()
