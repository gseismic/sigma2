"""sigma2 数据适配与 pyta2 指标共用同一条数值实现。"""

import numpy as np
import pytest
from pyta2.momentum import KDJ
from pyta2.relation import MACross
from pyta2.stats.atr import ATR
from pyta2.volume import MFI, OBV, VWAP

from sigma2 import (
    KlineATR, KlineKDJ, KlineMACross, KlineMFI, KlineOBV, KlineVWAP,
    rKlineMACross,
)


def make_data():
    close = np.array([10, 11, 12, 11, 13, 15, 14, 16, 15, 17, 18, 19], dtype=float)
    return {"open": close, "high": close + 1, "low": close - 1,
            "close": close, "volume": np.arange(1, len(close) + 1, dtype=float)}


@pytest.mark.parametrize("ma_type", ["SMA", "EMA"])
def test_atr_matches_pyta2_for_short_and_long_windows(ma_type):
    data = make_data()
    for n in (1, 3):
        got = KlineATR(data, n, ma_type=ma_type, return_type="tuple")
        expected = ATR(data["high"], data["low"], data["close"], n, ma_type)
        np.testing.assert_allclose(got, expected, equal_nan=True)


def test_kdj_cross_and_volume_match_pyta2():
    data = make_data()
    h, lo, c, v = (data[key] for key in ("high", "low", "close", "volume"))
    cases = (
        (KlineKDJ(data, 5, 3, 3, return_type="tuple"), KDJ(h, lo, c, 5, 3, 3)),
        (KlineMACross(data, 2, 4, ma_type="SMA", return_type="tuple"), MACross(c, 2, 4, "SMA")),
        ((KlineOBV(data, return_type="tuple"),), (OBV(c, v),)),
        ((KlineMFI(data, 3, return_type="tuple"),), (MFI(h, lo, c, v, 3),)),
        ((KlineVWAP(data, 3, return_type="tuple"),), (VWAP(h, lo, c, v, 3),)),
    )
    for actual, expected in cases:
        for actual_field, expected_field in zip(actual, expected, strict=True):
            np.testing.assert_allclose(actual_field, expected_field, equal_nan=True)


def test_kama_cross_recovers_after_missing_bar():
    signal = rKlineMACross(5, 10, ma_type="KAMA")
    outputs = []
    for index in range(90):
        price = np.nan if index == 35 else float(10 + index)
        outputs.append(signal.step({"open": price, "high": price, "low": price, "close": price}))
    assert np.isfinite(outputs[34][1:]).all()
    assert np.isnan(outputs[35][1:]).all()
    assert np.isfinite(outputs[65][1:]).all()
