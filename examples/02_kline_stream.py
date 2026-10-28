"""逐根推进 K 线并与批量重放比较：运行 python -m examples.02_kline_stream。"""

from sigma2 import KlineMA, rKlineMA
from examples._data import make_bars


def main() -> None:
    signal = rKlineMA(3, ma_type="SMA", return_dict=True)
    finalized = make_bars([10.0, 20.0, 33.0, 40.0])
    for item in finalized:
        print("新 K 线：", signal.step(item))
    print("索引与缓存行数：", signal.g_index, len(signal.outputs))
    batch = KlineMA(finalized, 3, ma_type="SMA")
    print("批量重放最后值：", batch[signal.factor_names[0]][-1])
    print("逐条输出 schema key：", signal.output_keys)
    signal.reset()
    print("重置后索引：", signal.g_index)


if __name__ == "__main__":
    main()
