from __future__ import annotations

import numpy as np
import pytest
from pyta2.base import rIndicator
from pyta2.base.schema import Schema
from pyta2.utils.space import Scalar

from sigma2 import forward_outcome_apply, rOutcome, rSignal
from sigma2.kline import rKlineFutureReturn
from tests.helpers import bars_from_columns


def scalar():
    return Scalar(low=-np.inf, high=np.inf, dtype=np.float64)


class rSigmaEcho(rSignal):
    name = "echo"

    def __init__(self, schema=None, **kwargs):
        super().__init__(
            {"value": scalar()} if schema is None else schema, n_backward=1, **kwargs
        )

    def forward(self, value):
        return value

    @property
    def full_name(self):
        return self.name


class rPytaEcho(rIndicator):
    name = "echo"

    def __init__(self, schema=None, **kwargs):
        super().__init__(
            {"value": scalar()} if schema is None else schema, n_backward=1, **kwargs
        )

    def forward(self, values):
        return values[-1]

    @property
    def full_name(self):
        return self.name


@pytest.mark.parametrize(
    "schema", [[("value", scalar())], {"value": scalar()}, Schema({"value": scalar()})]
)
@pytest.mark.parametrize("buffer_size", [None, 0, 1, 2, -1])
def test_operator_schema_output_and_buffer_match_pyta(schema, buffer_size):
    left = rSigmaEcho(schema, buffer_size=buffer_size, return_dict=True)
    right = rPytaEcho(schema, buffer_size=buffer_size, return_dict=True)
    for value in [1.5, 2.5, 3.5]:
        assert left.step(value) == right.rolling(np.array([value]))
        assert left.g_index == right.g_index
        assert left.result_index == right.result_index
        assert left.n_backward == right.n_backward
        assert left.n_forward == right.n_forward
        assert left.min_periods == right.min_periods
    assert left.output_keys == right.output_keys
    if left.outputs is None:
        assert right.outputs is None
    else:
        np.testing.assert_allclose(left.outputs["value"], right.outputs["value"])


def test_operator_rejects_dtype_shorthand_as_pyta_does():
    for cls in (rSigmaEcho, rPytaEcho):
        with pytest.raises(ValueError, match="Space"):
            cls({"value": np.float64})


def test_outcome_time_configuration_requires_positive_future_period():
    class rFutureEcho(rOutcome):
        def __init__(self, forward):
            super().__init__({"value": scalar()}, n_backward=0, n_forward=forward)

        def forward(self, value):
            return value

        @property
        def full_name(self):
            return "future_echo"

    with pytest.raises((TypeError, ValueError), match="n_forward"):
        rFutureEcho(0)
    with pytest.raises((TypeError, ValueError), match="n_forward"):
        rFutureEcho(True)
    outcome = rFutureEcho(2)
    assert outcome.result_index == -3
    assert outcome.step(10) == 10
    assert outcome.result_index == -2
    with pytest.raises(AttributeError):
        outcome.n_forward = 3


def test_short_and_empty_outcome_batches_have_no_mature_rows():
    bars = bars_from_columns(
        {key: [10, 11] for key in ("open", "high", "low", "close", "volume")}
    )
    result = forward_outcome_apply(
        bars, rKlineFutureReturn, param_args=(3,), return_type="tuple"
    )
    assert result.shape == (2,) and np.isnan(result).all()
    empty = forward_outcome_apply(
        [], rKlineFutureReturn, param_args=(3,), return_type="tuple"
    )
    assert empty.shape == (0,)


def test_failed_reset_stays_faulted_until_a_successful_reset():
    class rResetFail(rSigmaEcho):
        fail_reset = False

        def reset_extras(self):
            if self.fail_reset:
                raise ValueError("reset failed")

    signal = rResetFail()
    signal.step(1)
    signal.fail_reset = True
    with pytest.raises(ValueError, match="reset failed"):
        signal.reset()
    assert signal.is_faulted
    with pytest.raises(RuntimeError, match="reset"):
        signal.step(2)
    signal.fail_reset = False
    signal.reset()
    assert not signal.is_faulted and signal.g_index == -1
    assert signal.step(2) == 2
