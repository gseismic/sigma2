"""不调用 pyta2 指标的两级均值 Signal：在 examples 目录运行 python 07_mean_of_mean.py。"""

from sigma2.kline import KlineMeanOfMean, rKlineMeanOfMean

if __package__:
    from ._data import make_bars
else:
    from _data import make_bars


def main() -> None:
    signal = rKlineMeanOfMean(inner_n=2, outer_n=2, return_dict=True)
    data = make_bars([1.0, 2.0, 3.0, 5.0, 4.0])
    for bar in data:
        print("新 K 线：", bar.close, signal.step(bar))
    print("列名：", signal.factor_names)

    print("批量重放：", KlineMeanOfMean(data, inner_n=2, outer_n=2))


if __name__ == "__main__":
    main()
