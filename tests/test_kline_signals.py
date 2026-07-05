from __future__ import annotations

import math

import numpy as np
import pytest
from pyta2.utils.space import Scalar

from sigma2 import rGap, rKlineSignal, rReturn, rSMA


class rCloseEcho(rKlineSignal):
    name = "close_echo"

    def __init__(self, **kwargs):
        super().__init__(
            window=1,
            schema=[("close", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            **kwargs,
        )

    def reset_extras(self):
        pass

    def forward(self, open, high, low, close, volume):
        return close

    @property
    def full_name(self):
        return "close_echo"


def test_kline_signal_accepts_keyword_only_standard_ohlcv_input():
    signal = rCloseEcho(return_dict=True)

    assert signal.step(open=1.0, high=2.0, low=0.5, close=1.5, volume=100.0) == {
        "close": 1.5
    }
    assert signal.g_index == 0
    assert not hasattr(signal, "_window")

    with pytest.raises(TypeError):
        signal.step(1.0, 2.0, 0.5, 1.5, 100.0)


def test_forward_direct_call_on_kline_signal_does_not_advance_state():
    signal = rCloseEcho()

    assert signal.forward(1.0, 2.0, 0.5, 1.5, 100.0) == 1.5
    assert signal.g_index == -1
    assert len(signal.outputs) == 0


def test_return_signal_uses_close_to_close_window():
    signal = rReturn(n=1)

    assert math.isnan(signal.step(open=10.0, high=11.0, low=9.0, close=10.0, volume=1.0))
    assert signal.step(open=11.0, high=12.0, low=10.0, close=11.0, volume=1.0) == pytest.approx(
        0.1
    )

    assert signal.output_keys == ["return"]
    assert signal.full_name == "return(1)"


def test_gap_signal_uses_open_against_previous_close():
    signal = rGap(return_dict=True)

    first = signal.step(open=10.0, high=11.0, low=9.0, close=10.0, volume=1.0)
    second = signal.step(open=10.5, high=11.0, low=10.0, close=10.8, volume=1.0)

    assert math.isnan(first["gap"])
    assert second == {"gap": pytest.approx(0.05)}


def test_kline_window_signal_keeps_required_window_only():
    signal = rSMA(n=3, field="close")
    closes = [1.0, 2.0, 3.0, 4.0, 5.0]
    outputs = [
        signal.step(open=x, high=x, low=x, close=x, volume=1.0)
        for x in closes
    ]

    assert math.isnan(outputs[0])
    assert math.isnan(outputs[1])
    assert outputs[2:] == [pytest.approx(2.0), pytest.approx(3.0), pytest.approx(4.0)]
    assert len(signal._window) == signal.required_window == 3
    assert signal._window["close"].tolist() == [3.0, 4.0, 5.0]


def test_forward_direct_call_on_window_signal_does_not_mutate_internal_window():
    signal = rSMA(n=2)
    values = np.asarray([1.0, 2.0])

    assert signal.forward(values, values, values, values, values) == 1.5
    assert signal.g_index == -1
    assert len(signal.outputs) == 0
    assert len(signal._window) == 0


def test_sma_can_bind_to_supported_kline_fields():
    volume_sma = rSMA(n=2, field="volume")

    assert math.isnan(volume_sma.step(open=1.0, high=1.0, low=1.0, close=1.0, volume=10.0))
    assert volume_sma.step(open=1.0, high=1.0, low=1.0, close=1.0, volume=20.0) == 15.0

    with pytest.raises(ValueError, match="field must be one of"):
        rSMA(n=2, field="amount")
