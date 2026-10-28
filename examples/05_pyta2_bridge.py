"""将 pyta2 rolling 指标绑定到 K 线：运行 python -m examples.05_pyta2_bridge。"""

from pyta2.trend.ma.sma import rSMA

from examples._data import make_bars
from sigma2 import forward_signal_apply, pyta2_signal, rPyta2Signal


def main() -> None:
    signal = pyta2_signal(rSMA, params={"n": 2}, field="close", history_window=2)
    bars = make_bars([10.0, 11.0, 12.0, 15.0])
    for bar in bars:
        value = signal.step(bar)
    print("在线因子：", signal.full_name, value)
    batch = forward_signal_apply(
        bars,
        rPyta2Signal,
        param_args=(rSMA,),
        param_kwargs={"params": {"n": 2}, "field": "close", "history_window": 2},
    )
    print("批量最后值：", batch[signal.factor_names[0]][-1])


if __name__ == "__main__":
    main()
