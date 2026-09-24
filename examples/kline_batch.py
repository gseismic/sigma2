"""批量计算 K 线因子：从仓库根目录运行 python -m examples.kline_batch。"""

from sigma2 import KlineMA, KlineMACD


def main() -> None:
    closes = [10.0, 11.0, 12.0, 11.5, 13.0, 14.0, 13.5, 15.0]
    bars = {
        "open": [price - 0.2 for price in closes],
        "high": [price + 0.5 for price in closes],
        "low": [price - 0.5 for price in closes],
        "close": closes,
        "volume": [100.0 + 10 * index for index in range(len(closes))],
    }

    ma_columns, ma_meta = KlineMA(bars, 3, ma_type="EMA", return_meta_info=True)
    volume_ma = KlineMA(bars, 3, ma_type="SMA", field="volume")
    macd_columns = KlineMACD(bars, fast=2, slow=4, signal=2)

    ma_name = ma_meta["factor_names"][0]
    print("均线列名：", ma_name)
    print("最近三根均线：", ma_columns[ma_name][-3:])
    print("最近一根成交量均线：", volume_ma["SMA(3)[volume]"][-1])
    print("MACD 列名：", list(macd_columns))
    print(
        "最近一根 MACD：",
        {name: round(float(values[-1]), 4) for name, values in macd_columns.items()},
    )


if __name__ == "__main__":
    main()
