from __future__ import annotations

import math

import numpy as np
import pytest
from pyta2.stats.atr import rATR

from sigma2 import (
    pyta2_signal,
    rKlineATR,
    rKlineATRBoundTrigger,
    rKlineBoll,
    rKlineBundleFixedWeightIndex,
    rKlineBundleMarketCapWeightedIndex,
    rKlineBundleReturnRank,
    rKlineFutureChange,
    rKlineFutureHighLowChange,
    rKlineFutureReturn,
    rKlineKDJ,
    rKlineMA,
    rKlineMACD,
    rKlineMACross,
    rKlineMFI,
    rKlineRSI,
    rKlineReturn,
    rKlineVWAP,
)


@pytest.mark.parametrize(
    ("operator", "removed"),
    [
        (rKlineMA(2), ("field", "n", "ma_type")),
        (rKlineRSI(2), ("field", "n")),
        (rKlineATR(2), ("n", "ma_type")),
        (rKlineBoll(2), ("field", "n", "F")),
        (rKlineMACD(2, 4, 2), ("field", "fast", "slow", "signal")),
        (rKlineMACross(2, 4), ("field", "fast", "slow", "ma_type", "stride")),
        (rKlineKDJ(), ("n1", "n2", "n3", "ktimes", "dtimes")),
        (rKlineMFI(2), ("n",)),
        (rKlineVWAP(2), ("n", "ma_type")),
        (rKlineReturn(2), ("lag",)),
        (rKlineFutureChange(1), ("field",)),
        (rKlineFutureReturn(1), ("field", "return_type")),
        (rKlineFutureHighLowChange(1), ("reference_field",)),
        (
            rKlineATRBoundTrigger(1, 1, 1),
            ("x_unit_ub", "x_unit_lb", "atr_n", "atr_ma_type"),
        ),
        (
            pyta2_signal("SMA", history_window=2, params={"n": 2}),
            ("fields", "history_window"),
        ),
        (rKlineBundleReturnRank(), ("lag", "ascending")),
        (rKlineBundleFixedWeightIndex({"A": 1}), ("field", "weights")),
        (rKlineBundleMarketCapWeightedIndex(), ("field",)),
    ],
)
def test_config_readback_properties_are_not_exposed(operator, removed):
    assert all(not hasattr(operator, name) for name in removed)
    assert operator.full_name
    assert operator.meta_info["full_name"] == operator.full_name


@pytest.mark.parametrize(
    "factory",
    [
        lambda field: rKlineMA(3, field=field),
        lambda field: rKlineRSI(3, field=field),
        lambda field: rKlineBoll(3, field=field),
        lambda field: rKlineMACD(2, 4, 2, field=field),
        lambda field: rKlineMACross(2, 4, field=field),
        lambda field: pyta2_signal(
            "SMA", history_window=3, params={"n": 3}, field=field
        ),
    ],
)
def test_nondefault_field_drives_calculation_and_name(factory):
    volume_signal = factory("volume")
    close_signal = factory("close")
    assert volume_signal.full_name == close_signal.full_name.replace(
        "[close]", "[volume]"
    )
    observed_finite = False
    for index in range(15):
        volume = 10 + index**2
        bar = {"open": 1, "high": 2, "low": 0, "close": 1, "volume": volume}
        actual = volume_signal.step(**bar)
        reference = close_signal.step(**{**bar, "close": volume})
        assert actual.keys() == reference.keys()
        for key in actual:
            np.testing.assert_allclose(actual[key], reference[key], equal_nan=True)
            observed_finite |= bool(np.any(np.isfinite(actual[key])))
    assert observed_finite


def test_pyta2_multiple_inputs_and_window_keep_working():
    adapter = pyta2_signal(
        rATR,
        history_window=2,
        params={"n": 3, "ma_type": "SMA"},
        inputs=("high", "low", "close"),
    )
    reference = rKlineATR(3, ma_type="SMA")
    assert adapter.full_name == reference.full_name == "ATR(3,SMA)[high,low,close]"
    for value in range(1, 8):
        bar = {"open": value, "high": value + 2, "low": value - 1, "close": value + 1}
        actual = adapter.step(**bar)
        expected = reference.step(**bar)
        np.testing.assert_allclose(actual["atr"], expected["atr"], equal_nan=True)


def test_outcome_configuration_still_controls_results_and_names():
    change = rKlineFutureChange(1, field="volume")
    future_return = rKlineFutureReturn(1, field="open", return_type="LOG")
    high_low = rKlineFutureHighLowChange(1, reference_field="open")
    first = {"open": 10, "high": 12, "low": 9, "close": 100, "volume": 5}
    second = {"open": 15, "high": 20, "low": 13, "close": 90, "volume": 15}
    for outcome in (change, future_return, high_low):
        outcome.step(**first)
    assert change.step(**second) == {"value": 10.0}
    assert future_return.step(**second)["log_return"] == pytest.approx(math.log(1.5))
    assert high_low.step(**second) == {"high_change": 10.0, "low_change": 3.0}
    assert change.full_name == "kline_future_change(volume,1)"
    assert future_return.full_name == "kline_future_return(open,1,return_type=log)"
    assert high_low.full_name == "kline_future_high_low_change(open,1)"
    bound = rKlineATRBoundTrigger(1.5, 0.5, 2, atr_n=3, atr_ma_type="SMA")
    assert bound.full_name == (
        "kline_atr_bound_trigger(x_unit_ub=1.5,x_unit_lb=0.5,"
        "n_forward=2,atr_n=3,atr_ma_type=SMA)"
    )


def test_lag_ranking_direction_and_weights_still_control_results():
    returns = rKlineReturn(2)
    for close in (10, 20):
        returns.step(open=1, high=2, low=0, close=close)
    assert returns.step(open=1, high=2, low=0, close=40) == {"return": 3.0}
    assert returns.full_name == "return(2)"

    rank = rKlineBundleReturnRank(2, ascending=False)
    rank.step({"A": {"close": 100}, "B": {"close": 100}})
    rank.step({"A": {"close": 200}, "B": {"close": 50}})
    assert rank.step({"A": {"close": 110}, "B": {"close": 90}}) == {
        "rank": {"A": 1, "B": 2}
    }
    assert rank.full_name == "ReturnRank(2,ascending=False)"

    bundle = {
        "A": {"open": 10, "close": 100, "market_cap": 1},
        "B": {"open": 30, "close": 200, "market_cap": 3},
    }
    fixed = rKlineBundleFixedWeightIndex({"A": 1, "B": 3}, field="open")
    market_cap = rKlineBundleMarketCapWeightedIndex(field="open")
    assert fixed.step(bundle) == market_cap.step(bundle) == {"index": 25.0}
    assert fixed.full_name == "FixedWeightIndex(open,weights={'A': 1.0, 'B': 3.0})"
    assert market_cap.full_name == "MarketCapWeightedIndex(open)"
