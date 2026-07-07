from __future__ import annotations

import math

import pytest

from sigma2.kline.effect import (
    rKlineBoundTrigger,
    rKlineFutureChange,
    rKlineFutureHighLowChange,
    rKlineFutureReturn,
)


def _step(signal, open_, high, low, close, volume=1.0):
    return signal.step(open=open_, high=high, low=low, close=close, volume=volume)


def test_kline_future_return_outputs_delayed_anchor_target():
    signal = rKlineFutureReturn(2, return_dict=True)

    outputs = [
        _step(signal, 10.0, 10.0, 10.0, 10.0),
        _step(signal, 11.0, 11.0, 11.0, 11.0),
        _step(signal, 13.0, 13.0, 13.0, 13.0),
        _step(signal, 12.0, 12.0, 12.0, 12.0),
    ]

    assert math.isnan(outputs[0]["return"])
    assert math.isnan(outputs[1]["return"])
    assert outputs[2]["return"] == pytest.approx(0.3)
    assert outputs[3]["return"] == pytest.approx(12.0 / 11.0 - 1.0)
    assert signal.family == "kline"
    assert signal.step_input_keys == ("open", "high", "low", "close", "volume")


def test_kline_future_change_can_bind_to_open_field():
    signal = rKlineFutureChange(1, field="open")

    assert math.isnan(_step(signal, 10.0, 11.0, 9.0, 10.5))
    assert _step(signal, 12.0, 13.0, 11.0, 12.5) == 2.0


def test_kline_future_high_low_change_uses_standard_kline_window():
    signal = rKlineFutureHighLowChange(2, return_dict=True)

    first = _step(signal, 100.0, 101.0, 99.0, 100.0)
    second = _step(signal, 102.0, 105.0, 100.0, 102.0)
    third = _step(signal, 101.0, 103.0, 98.0, 101.0)

    assert math.isnan(first["high_change"])
    assert math.isnan(second["low_change"])
    assert third == {"high_change": 5.0, "low_change": -2.0}


def test_kline_bound_trigger_uses_unit_field_and_ohlc_path():
    signal = rKlineBoundTrigger(upper=0.05, lower=0.02, horizon=2, return_dict=True)

    first = _step(signal, 100.0, 100.0, 100.0, 100.0)
    second = _step(signal, 101.0, 106.0, 100.0, 104.0)
    third = _step(signal, 102.0, 103.0, 99.0, 101.0)

    assert first == {"trigger": 0, "unit_change": 0.0, "trigger_index": -1}
    assert second == {"trigger": 0, "unit_change": 0.0, "trigger_index": -1}
    assert third == {"trigger": 1, "unit_change": 0.05, "trigger_index": 1}


def test_kline_effect_rejects_unknown_field():
    with pytest.raises(ValueError, match="unknown kline input field"):
        rKlineFutureReturn(1, field="amount")

    with pytest.raises(ValueError, match="unknown kline input field"):
        rKlineBoundTrigger(upper=0.05, lower=0.02, horizon=1, unit_field="amount")
