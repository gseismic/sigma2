"""批量计算 K 线因子：在 examples 目录运行 python 01_kline_batch.py。"""

from sigma2 import KlineMA, KlineMACD


def main() -> None:
    closes = [10.0, 11.0, 12.0, 11.5, 13.0, 14.0, 13.5, 15.0]
    bars = [
        {
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 100.0 + 10 * index,
            "open_time": index,
        }
        for index, close in enumerate(closes)
    ]

    ma_columns, ma_meta = KlineMA(bars, 3, ma_type="EMA", return_meta_info=True)
    volume_ma = KlineMA(bars, 3, ma_type="SMA", field="volume")
    macd_columns = KlineMACD(bars, fast=2, slow=4, signal=2)

    print("均线公式：", ma_meta["full_name"])
    print("最近三根均线：", ma_columns["ma"][-3:])
    print("最近一根成交量均线：", volume_ma["ma"][-1])
    print("MACD 列名：", list(macd_columns))
    print(
        "最近一根 MACD：",
        {name: round(float(values[-1]), 4) for name, values in macd_columns.items()},
    )


if __name__ == "__main__":
    main()
