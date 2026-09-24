"""在线推进与修订最后一根 K 线：运行 python -m examples.02_kline_stream。"""

from sigma2 import KlineMA, rKlineMA


def bar(close: float) -> dict[str, float]:
    return {
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": 1.0,
    }


def main() -> None:
    signal = rKlineMA(3, ma_type="SMA", return_dict=True)
    confirmed = [bar(10.0), bar(20.0)]
    for item in confirmed:
        signal.step(**item)

    signal.step(**bar(30.0))
    revised = bar(33.0)
    print("首次修订：", signal.update_last(**revised))
    print("重复修订：", signal.update_last(**revised))
    print("索引与缓存行数：", signal.g_index, len(signal.outputs))

    next_bar = bar(40.0)
    print("下一根输出：", signal.step(**next_bar))

    finalized = confirmed + [revised, next_bar]
    columns = {key: [item[key] for item in finalized] for key in finalized[0]}
    batch = KlineMA(columns, 3, ma_type="SMA")
    print("批量重放最后值：", batch[signal.factor_names[0]][-1])
    print("逐条输出 schema key：", signal.output_keys)


if __name__ == "__main__":
    main()
