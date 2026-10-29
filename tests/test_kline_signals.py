from __future__ import annotations

import math

import numpy as np
import pytest
from pyta2.utils.space import Scalar

from sigma2.kline import rKlineGap, rKlineMA, rKlineReturn, rKlineSignal
from tests.helpers import make_bar


class rCloseEcho(rKlineSignal):
    name = "close_echo"

    def __init__(self, **kwargs):
        super().__init__(
            n_backward=0,
            schema=[("close", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            **kwargs,
        )

    def forward(self, bar):
        return bar.close

    @property
    def full_name(self):
        return "close_echo"


def test_kline_signal_accepts_a_bar_object_and_checks_stream():
    signal = rCloseEcho(return_dict=True)
    bar = make_bar(open=1, high=2, low=0.5, close=1.5, volume=100)
    assert signal.step(bar) == {"close": 1.5}
    assert signal.g_index == 0
    assert not hasattr(signal, "_window")
    with pytest.raises(TypeError):
        signal.step(open=1, high=2, low=0.5, close=1.5, volume=100)
    with pytest.raises(ValueError, match="strictly increasing"):
        signal.step(bar)
    with pytest.raises(ValueError, match="symbol"):
        signal.step(make_bar(open=1, high=2, low=0.5, close=1.5, symbol="B"))
    assert not signal.is_faulted
    assert signal.g_index == 0


def test_forward_direct_call_on_kline_signal_does_not_advance_state():
    signal = rCloseEcho()
    assert signal.forward(make_bar(open=1, high=2, low=0.5, close=1.5)) == 1.5
    assert signal.g_index == -1
    assert len(signal.outputs) == 0


def test_return_signal_uses_close_to_close_window():
    signal = rKlineReturn(n=1)
    assert math.isnan(signal.step(make_bar(open=10, high=11, low=9, close=10)))
    assert signal.step(make_bar(open=11, high=12, low=10, close=11)) == pytest.approx(
        0.1
    )
    assert signal.output_keys == ["return"]
    assert signal.full_name == "return(1)"


def test_gap_signal_uses_open_against_previous_close():
    signal = rKlineGap(return_dict=True)
    first = signal.step(make_bar(open=10, high=11, low=9, close=10))
    second = signal.step(make_bar(open=10.5, high=11, low=10, close=10.8))
    assert math.isnan(first["gap"])
    assert second == {"gap": pytest.approx(0.05)}


def test_kline_window_signal_keeps_required_history_only():
    signal = rKlineMA(n=3, ma_type="SMA", field="close")
    outputs = [
        signal.step(make_bar(open=x, high=x, low=x, close=x)) for x in [1, 2, 3, 4, 5]
    ]
    assert np.isnan(outputs[:2]).all()
    assert outputs[2:] == pytest.approx([2, 3, 4])
    assert len(signal._window) == signal.history_window == 3
    assert [bar.close for bar in signal._window] == [3, 4, 5]


def test_forward_direct_call_on_window_signal_does_not_mutate_input_window():
    signal = rKlineMA(n=2, ma_type="SMA")
    values = np.asarray([1.0, 2.0])
    assert signal.forward(values, values, values, values, values) == 1.5
    assert signal.g_index == -1
    assert len(signal.outputs) == 0
    assert len(signal._window) == 0


def test_ma_can_bind_to_supported_kline_fields():
    signal = rKlineMA(n=2, ma_type="SMA", field="volume")
    assert math.isnan(signal.step(make_bar(open=1, high=1, low=1, close=1, volume=10)))
    assert signal.step(make_bar(open=1, high=1, low=1, close=1, volume=20)) == 15
    with pytest.raises(ValueError, match="unknown kline input field"):
        rKlineMA(n=2, ma_type="SMA", field="amount")
