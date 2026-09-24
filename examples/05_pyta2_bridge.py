"""把 pyta2 rolling 指标绑定 K 线字段：运行 python -m examples.05_pyta2_bridge。"""

from pyta2.momentum import rROC

from sigma2 import forward_signal_apply, pyta2_signal, rPyta2Signal


def bar(close: float) -> dict[str, float]:
    return {
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": 1.0,
    }


def main() -> None:
    signal = pyta2_signal(rROC, params={"n": 2}, field="close")
    rows = [bar(close) for close in (10.0, 11.0, 12.0, 15.0)]
    for row in rows:
        value = signal.step(**row)
    print("在线因子：", signal.full_name, value)

    columns = {key: [row[key] for row in rows] for key in rows[0]}
    batch = forward_signal_apply(
        columns,
        rPyta2Signal,
        param_args=(rROC,),
        param_kwargs={"params": {"n": 2}, "field": "close"},
    )
    print("批量最后值：", batch[signal.factor_names[0]][-1])


if __name__ == "__main__":
    main()
