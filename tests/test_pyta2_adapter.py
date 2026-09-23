from __future__ import annotations

import math

import pytest

from sigma2.core import pyta2_signal, rPyta2Signal
from sigma2.utils.pyta2 import resolve_pyta2_indicator


def test_resolve_pyta2_indicator_name_to_rolling_class():
    cls = resolve_pyta2_indicator("SMA")

    assert cls.__name__ == "rSMA"


def test_generic_adapter_returns_pyta2_step_signal():
    signal = rPyta2Signal(
        "SMA",
        params={"n": 3},
        field="close",
        return_dict=True,
    )

    assert isinstance(signal, rPyta2Signal)
    assert signal.family == "kline"
    assert signal.inputs == ("close",)
    assert signal.output_keys == ["ma"]
    assert signal.full_name == "SMA(3)[close]"

    outputs = [
        signal.step(open=x, high=x, low=x, close=x, volume=1.0)
        for x in [1.0, 2.0, 3.0, 4.0]
    ]

    assert math.isnan(outputs[0]["ma"])
    assert math.isnan(outputs[1]["ma"])
    assert outputs[2:] == [{"ma": 2.0}, {"ma": 3.0}]
    assert signal.g_index == 3
    assert signal._indicator.g_index == 3


def test_pyta2_signal_can_bind_to_kline_field_by_name():
    signal = pyta2_signal("SMA", params={"n": 2}, field="high")

    assert math.isnan(signal.step(open=1.0, high=10.0, low=1.0, close=1.0, volume=1.0))
    assert signal.step(open=1.0, high=20.0, low=1.0, close=1.0, volume=1.0) == 15.0
    assert signal.inputs == ("high",)


def test_pyta2_adapter_rejects_unknown_indicator_or_input_field():
    with pytest.raises(ValueError, match="unknown pyta2 indicator"):
        pyta2_signal("NOT_A_SIGNAL")

    with pytest.raises(ValueError, match="unknown kline input field"):
        rPyta2Signal("SMA", params={"n": 2}, field="amount")

    with pytest.raises(ValueError, match="cannot both be provided"):
        rPyta2Signal("SMA", params={"n": 2}, field="close", inputs=("close",))
