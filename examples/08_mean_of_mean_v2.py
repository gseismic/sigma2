"""pyta2 MA 两级组合：运行 python -m examples.08_mean_of_mean_v2。"""

from sigma2.kline import KlineMeanOfMeanV2, rKlineMeanOfMeanV2
from examples._data import make_bars


def main() -> None:
    signal = rKlineMeanOfMeanV2(2, 2, ma_type="EMA", return_dict=True)
    data = make_bars([1.0, 2.0, 3.0, 5.0, 4.0])
    for bar in data:
        print("新 K 线：", bar.close, signal.step(bar))
    print("列名：", signal.factor_names)

    print("批量重放：", KlineMeanOfMeanV2(data, 2, 2, ma_type="EMA"))


if __name__ == "__main__":
    main()
