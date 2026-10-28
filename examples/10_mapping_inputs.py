"""字典输入和字段映射：在 examples 目录运行 python 10_mapping_inputs.py。"""

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.kline import KlineMA, rKlineSignal
from sigma2.kline_bundle import rKlineBundleRank


class rCloseWithDate(rKlineSignal):
    """读取逻辑字段 date，并返回收盘价。"""

    def __init__(self, **kwargs):
        super().__init__(
            {"close": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            n_backward=0,
            required_fields=("date",),
            **kwargs,
        )

    def reset_extras(self):
        self.last_date = None

    def forward(self, bar):
        self.last_date = bar["date"]
        return float(bar["close"])

    @property
    def full_name(self):
        return "close_with_date"


def main() -> None:
    bars = [
        {
            "open": 100,
            "high": 101,
            "low": 99,
            "close": 100,
            "open_time": 1,
            "trade_volume": 10,
            "extra": "保留",
        },
        {
            "open": 110,
            "high": 111,
            "low": 109,
            "close": 110,
            "open_time": 2,
            "trade_volume": 20,
            "extra": "保留",
        },
    ]

    signal = rCloseWithDate(key_map={"date": "open_time"})
    for item in bars:
        value = signal.step(item)
        print("时间与收盘价：", signal.last_date, value)

    values, meta = KlineMA(
        bars,
        2,
        field="volume",
        key_map={"volume": "trade_volume", "bar_time": "open_time"},
        return_meta_info=True,
    )
    print("成交量均线：", values)
    print("输入时间和映射：", meta["bar_times"], meta["key_map"])

    bundle = {
        "open_time": 2,
        "bars": {
            "BTC": {"open": 110, "high": 111, "low": 109, "close": 110},
            "ETH": {"open": 200, "high": 201, "low": 199, "close": 200},
        },
    }
    rank = rKlineBundleRank(
        symbols=("BTC", "ETH", "SOL"),
        bundle_key_map={"bar_time": "open_time"},
    )
    print("截面排名：", rank.step(bundle))
    print("截面时间：", rank.meta_info["last_bar_time"])


if __name__ == "__main__":
    main()
