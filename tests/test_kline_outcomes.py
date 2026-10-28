from __future__ import annotations

import math

import numpy as np
import pytest

from sigma2 import forward_outcome_apply
from sigma2.kline.outcome import (
    rKlineATRBoundTrigger,
    rKlineFutureChange,
    rKlineFutureHighLowChange,
    rKlineFutureReturn,
)
from tests.helpers import make_bar


def _step(signal, open_, high, low, close, volume=1.0):
    return signal.step(
        make_bar(open=open_, high=high, low=low, close=close, volume=volume)
    )


def test_kline_future_return_outputs_delayed_anchor():
    signal = rKlineFutureReturn(2, return_dict=True)
    outputs = [_step(signal, x, x, x, x) for x in [10, 11, 13, 12]]
    assert math.isnan(outputs[0]["return"])
    assert math.isnan(outputs[1]["return"])
    assert outputs[2]["return"] == pytest.approx(0.3)
    assert outputs[3]["return"] == pytest.approx(12 / 11 - 1)
    assert signal.result_index == 1
    assert signal.step_input_keys == ("bar",)


def test_kline_future_log_return():
    signal = rKlineFutureReturn(1, return_type="log", return_dict=True)
    assert math.isnan(_step(signal, 10, 10, 10, 10)["log_return"])
    assert _step(signal, 11, 11, 11, 11)["log_return"] == pytest.approx(math.log(1.1))


def test_kline_future_change_can_bind_to_open_field():
    signal = rKlineFutureChange(1, field="open", return_dict=True)
    assert math.isnan(_step(signal, 10, 11, 9, 10.5)["value"])
    assert _step(signal, 12, 13, 11, 12.5) == {"value": 2.0}


def test_future_return_and_change_require_complete_future_window():
    bars = [make_bar(open=x, high=x, low=x, close=x) for x in [10, np.nan, 12, 13, 14]]
    for outcome_type in (rKlineFutureReturn, rKlineFutureChange):
        outcome = outcome_type(2)
        values = [outcome.step(bar) for bar in bars]
        assert np.isnan(values[:4]).all()
        assert np.isfinite(values[4])
        columns, meta = forward_outcome_apply(
            bars, outcome_type, param_args=(2,), return_meta_info=True
        )
        aligned = columns[outcome.factor_names[0]]
        assert np.isnan(aligned[:2]).all()
        assert aligned[2] == pytest.approx(values[4])
        assert np.isnan(aligned[-2:]).all()
        assert meta["emission_bar_times"][2] == bars[4].bar_time


def test_kline_future_high_low_change_uses_future_window():
    signal = rKlineFutureHighLowChange(2, return_dict=True)
    first = _step(signal, 100, 101, 99, 100)
    second = _step(signal, 102, 105, 100, 102)
    third = _step(signal, 101, 103, 98, 101)
    assert math.isnan(first["high_change"])
    assert math.isnan(second["low_change"])
    assert third == {"high_change": 5.0, "low_change": -2.0}


def test_kline_bound_trigger_uses_atr_units():
    signal = rKlineATRBoundTrigger(0.05, 0.02, 1, atr_n=1, return_dict=True)
    first = _step(signal, 100, 104, 100, 101)
    second = _step(signal, 101, 102, 99, 100)
    assert first == signal.make_dict_output(signal.missing_output)
    assert second == {"trigger": 1, "unit_change": 0.05, "trigger_location": 1}


def test_kline_atr_bound_trigger_aligns_anchor_after_atr_warmup():
    signal = rKlineATRBoundTrigger(
        1, 1, 1, atr_n=3, atr_ma_type="SMA", return_dict=True
    )
    outputs = [
        _step(signal, 100, high, 99 if high == 101 else 100, 100)
        for high in (101, 101, 101, 103)
    ]
    assert all(np.isnan(row["unit_change"]) for row in outputs[:3])
    assert outputs[3] == {"trigger": 1, "unit_change": 1, "trigger_location": 1}


def test_kline_atr_bound_trigger_validates_constructor_args():
    with pytest.raises(ValueError, match="x_unit_ub"):
        rKlineATRBoundTrigger(0, 1, 1)
    with pytest.raises(ValueError, match="n_forward"):
        rKlineATRBoundTrigger(1, 1, 0)
    with pytest.raises(ValueError, match="n_atr"):
        rKlineATRBoundTrigger(1, 1, 1, atr_n=0)


def test_kline_outcome_rejects_unknown_field():
    with pytest.raises(ValueError, match="unknown kline input field"):
        rKlineFutureReturn(1, field="amount")
