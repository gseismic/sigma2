from __future__ import annotations

import math

import pytest

from sigma2.kline.pyta2 import pyta2_signal, rPyta2Signal
from sigma2.utils.pyta2 import resolve_pyta2_indicator
from tests.helpers import make_bar


def test_resolve_pyta2_indicator_name_to_rolling_class():
    assert resolve_pyta2_indicator("SMA").__name__ == "rSMA"


def test_generic_adapter_returns_pyta2_step_signal():
    signal = rPyta2Signal(
        "SMA", history_window=3, params={"n": 3}, field="close", return_dict=True
    )
    assert signal.family == "kline"
    assert signal.fields == ("close",)
    assert signal.output_keys == ["ma"]
    assert signal.full_name == "SMA(3)[close]"
    outputs = [
        signal.step(make_bar(open=x, high=x, low=x, close=x)) for x in [1, 2, 3, 4]
    ]
    assert math.isnan(outputs[0]["ma"])
    assert math.isnan(outputs[1]["ma"])
    assert outputs[2:] == [{"ma": 2.0}, {"ma": 3.0}]
    assert signal.g_index == signal._indicator.g_index == 3


def test_pyta2_signal_can_bind_to_kline_field_by_name():
    signal = pyta2_signal("SMA", history_window=2, params={"n": 2}, field="high")
    assert math.isnan(signal.step(make_bar(open=1, high=10, low=1, close=1)))
    assert signal.step(make_bar(open=1, high=20, low=1, close=1)) == 15
    assert signal.fields == ("high",)


def test_pyta2_adapter_rejects_unknown_indicator_or_input_field():
    with pytest.raises(ValueError, match="unknown pyta2 indicator"):
        pyta2_signal("NOT_A_SIGNAL", history_window=2)
    with pytest.raises(ValueError, match="unknown kline input field"):
        rPyta2Signal("SMA", history_window=2, params={"n": 2}, field="amount")
    with pytest.raises(ValueError, match="cannot both be provided"):
        rPyta2Signal(
            "SMA", history_window=2, params={"n": 2}, field="close", inputs=("close",)
        )
    with pytest.raises(TypeError, match="pyta2 rIndicator"):
        rPyta2Signal(object, history_window=2)
    with pytest.raises(TypeError, match="history_window"):
        rPyta2Signal("SMA", params={"n": 2})
