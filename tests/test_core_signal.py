from __future__ import annotations

import math

import numpy as np
import pytest
from pyta2.utils.space import Scalar

from sigma2 import rSignal


class rEcho(rSignal):
    name = "echo"
    family = "test"
    step_input_keys = ("value",)

    def __init__(self, window=1, **kwargs):
        self.reset_count = 0
        super().__init__(
            window=window,
            schema=[("value", Scalar(low=-np.inf, high=np.inf, dtype=np.float64))],
            **kwargs,
        )

    def reset_extras(self):
        self.reset_count += 1

    def forward(self, value):
        return value * 2

    @property
    def full_name(self):
        return "echo"


class rPair(rSignal):
    name = "pair"
    family = "test"
    step_input_keys = ("value",)

    def __init__(self, mode="tuple", **kwargs):
        self.mode = mode
        super().__init__(
            window=1,
            schema=[
                ("left", Scalar(low=-np.inf, high=np.inf, dtype=np.float64)),
                ("right", Scalar(low=-np.inf, high=np.inf, dtype=np.float64)),
            ],
            **kwargs,
        )

    def reset_extras(self):
        pass

    def forward(self, value):
        if self.mode == "tuple":
            return value, value + 1
        if self.mode == "mapping":
            return {"left": value, "right": value + 1}
        if self.mode == "bad_mapping":
            return {"left": value, "other": value + 1}
        if self.mode == "bad_arity":
            return (value,)
        return "bad-string"

    @property
    def full_name(self):
        return "pair"


def test_step_advances_lifecycle_and_caches_output():
    signal = rEcho()

    assert signal.g_index == -1
    assert signal.latest is None

    assert signal.step(3.0) == 6.0

    assert signal.g_index == 0
    assert len(signal.outputs) == 1
    assert signal.latest == {"value": 6.0}


def test_forward_direct_call_does_not_advance_lifecycle():
    signal = rEcho()

    assert signal.forward(3.0) == 6.0

    assert signal.g_index == -1
    assert len(signal.outputs) == 0
    assert signal.latest is None


def test_return_dict_uses_schema_keys():
    signal = rEcho(return_dict=True)

    assert signal.step(2.0) == {"value": 4.0}
    assert signal.latest == {"value": 4.0}


def test_output_buffer_can_be_bounded():
    signal = rEcho(buffer_size=2)

    signal.step(1.0)
    signal.step(2.0)
    signal.step(3.0)

    assert signal.g_index == 2
    assert len(signal.outputs) == 2
    assert signal.outputs.to_list() == [{"value": 4.0}, {"value": 6.0}]


def test_reset_clears_outputs_and_resets_extras():
    signal = rEcho()
    initial_reset_count = signal.reset_count
    signal.step(1.0)

    signal.reset()

    assert signal.g_index == -1
    assert len(signal.outputs) == 0
    assert signal.latest is None
    assert signal.reset_count == initial_reset_count + 1


def test_multi_output_tuple_and_mapping_are_normalized():
    tuple_signal = rPair()
    mapping_signal = rPair(mode="mapping", return_dict=True)

    assert tuple_signal.step(1.0) == (1.0, 2.0)
    assert tuple_signal.latest == {"left": 1.0, "right": 2.0}
    assert mapping_signal.step(2.0) == {"left": 2.0, "right": 3.0}


def test_output_schema_mismatch_raises_clear_errors():
    with pytest.raises(ValueError, match="output keys mismatch"):
        rPair(mode="bad_mapping").step(1.0)

    with pytest.raises(ValueError, match="output arity mismatch"):
        rPair(mode="bad_arity").step(1.0)

    with pytest.raises(TypeError, match="must not be string-like"):
        rPair(mode="bad_string").step(1.0)


def test_window_validation_and_meta_info():
    signal = rEcho(extra_window=2, name="custom_echo")

    assert signal.required_window == 3
    assert signal.meta_info["name"] == "custom_echo"
    assert signal.meta_info["family"] == "test"
    assert signal.meta_info["step_input_keys"] == ("value",)

    with pytest.raises(ValueError, match="window must be greater than 0"):
        rEcho(window=0)


def test_single_output_mapping_must_match_only_schema_key():
    class rBadSingle(rEcho):
        def forward(self, value):
            return {"other": value}

    with pytest.raises(ValueError, match="output keys mismatch"):
        rBadSingle().step(1.0)


def test_nan_output_is_cached_as_nan():
    class rNan(rEcho):
        def forward(self, value):
            return float("nan")

    signal = rNan()

    assert math.isnan(signal.step(1.0))
    assert math.isnan(signal.latest["value"])
