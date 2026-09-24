"""pyta2 MA 两级组合：运行 python -m examples.08_mean_of_mean_v2。"""

from sigma2.kline import KlineMeanOfMeanV2, rKlineMeanOfMeanV2


def _bar(close: float) -> dict[str, float]:
    return {
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": 1.0,
    }


def main() -> None:
    signal = rKlineMeanOfMeanV2(2, 2, ma_type="EMA", return_dict=True)
    for close in (1.0, 2.0, 3.0):
        print("新 K 线：", close, signal.step(**_bar(close)))

    print("修订末根：", signal.update_last(**_bar(5.0)))
    print("继续推进：", signal.step(**_bar(4.0)))
    print("列名：", signal.factor_names)

    closes = [1.0, 2.0, 5.0, 4.0]
    data = {key: closes for key in ("open", "high", "low", "close")}
    data["volume"] = [1.0] * len(closes)
    print("批量重放：", KlineMeanOfMeanV2(data, 2, 2, ma_type="EMA"))


if __name__ == "__main__":
    main()
