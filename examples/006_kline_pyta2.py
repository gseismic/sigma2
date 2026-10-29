"""pyta2 桥接：将一个 rolling 指标绑定到 K 线字段。"""

from pyta2.trend.ma.sma import rSMA

from sigma2 import forward_step_apply, pyta2_signal


def main() -> None:
    bars = [
        {"open": close, "high": close, "low": close, "close": close, "open_time": index}
        for index, close in enumerate([10.0, 11.0, 12.0, 15.0])
    ]
    signal = pyta2_signal(rSMA, params={"n": 2}, field="close", history_window=2)
    for bar in bars:
        print("在线指标：", signal.step(**bar))
    print("指标名称和使用字段：", signal.full_name, signal.meta_info["used_fields"])

    fresh = pyta2_signal(rSMA, params={"n": 2}, field="close", history_window=2)
    columns = forward_step_apply(bars, fresh)
    print("批量指标：", columns["ma"])


if __name__ == "__main__":
    main()
