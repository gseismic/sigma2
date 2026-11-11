from __future__ import annotations

import math

import numpy as np
import pytest

from sigma2 import (
    KlineMA,
    forward_step_apply,
    rBookSpread,
    rBundleSignal,
    rKlineBundleFixedWeightIndex,
    rKlineBundleReturnRank,
    rKlineMA,
    rTradeSignedVolume,
)


class WindowVolume(rBundleSignal):
    def forward(self, bundle, *, time=None):
        return {
            "volume": {
                symbol: sum(trade["volume"] for trade in trades)
                for symbol, trades in bundle.items()
            }
        }


class SumValues(rBundleSignal):
    def forward(self, bundle, *, time=None):
        return {"sum": sum(bundle.values())}


def test_kline_flat_calls_and_batch_still_match():
    rows = [
        {"open": value, "high": value, "low": value, "close": value, "open_time": index}
        for index, value in enumerate((10, 20, 30))
    ]
    signal = rKlineMA(2, ma_type="SMA")
    online = [signal.step(**row)["ma"] for row in rows]
    batch = KlineMA(rows, 2, ma_type="SMA")["ma"]
    np.testing.assert_allclose(online, [np.nan, 15, 25], equal_nan=True)
    np.testing.assert_allclose(batch, online, equal_nan=True)


def test_bundle_accepts_distinct_value_formats_and_empty_steps():
    windows = WindowVolume()
    assert windows.step({"BTC": [{"volume": 2}], "ETH": []}, time=1) == {
        "volume": {"BTC": 2, "ETH": 0}
    }
    assert windows.step({}, time=1) == {"volume": {}}
    assert windows.g_index == 1 and windows.family == "bundle"
    totals = SumValues()
    assert totals.step({"BTC": 1.5, "ETH": -0.5}) == {"sum": 1.0}
    assert rBookSpread().step(bids=[(99, 1)], asks=[(101, 1)]) == {"spread": 2.0}
    assert rTradeSignedVolume().step(price=1, volume=2, side="sell") == {
        "signed_volume": -2.0
    }


def test_rank_history_uses_common_time_and_survives_input_reuse():
    rank = rKlineBundleReturnRank(lag=1)
    bundle = {"BTC": {"close": 100}, "ETH": {"close": 200}}
    first = rank.step(bundle, open_time=0)["rank"]
    bundle["BTC"]["close"] = 110
    bundle["ETH"]["close"] = 190
    second = rank.step(bundle, open_time=1)["rank"]
    assert second == {"BTC": 2, "ETH": 1}
    assert all(math.isnan(value) for value in first.values())
    rank.step({}, open_time=2)
    third = rank.step(bundle, open_time=3)["rank"]
    assert all(math.isnan(value) for value in third.values())
    assert second == {"BTC": 2, "ETH": 1}


def test_tiny_weight_and_batch_follow_existing_contracts():
    index = rKlineBundleFixedWeightIndex({"A": 1.0, "B": 5e-324})
    result = index.step({"A": {"close": 0.0}, "B": {"close": 1e308}})["index"]
    assert result > 0
    assert result == pytest.approx(5e-324 * 1e308, rel=1e-12, abs=0.0)
    rows = [{"bundle": {"A": 1, "B": 2}}, {"bundle": {}}, {"bundle": {"B": 4}}]
    output = forward_step_apply(rows, SumValues(buffer_size=0))
    assert list(output["sum"]) == [3, 0, 4]
