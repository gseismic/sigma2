from __future__ import annotations

import math

import numpy as np
import pytest
from pyta2.trend.ma.api import get_ma_class, get_ma_function

from sigma2.kline import (
    KlineMeanOfMean,
    KlineMeanOfMeanV2,
    rKlineMeanOfMeanV2,
)


_MA_TYPES = ("SMA", "EMA", "WMA", "HMA", "DEMA", "TEMA", "KAMA", "ZLEMA")


def _data(length: int = 120) -> dict[str, np.ndarray]:
    index = np.arange(length, dtype=np.float64)
    close = 100.0 + index * 0.1 + np.sin(index / 3.0)
    return {
        "open": close + 0.25,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": close * 10.0,
    }


def _bar(value: float) -> dict[str, float]:
    return {key: value for key in ("open", "high", "low", "close", "volume")}


@pytest.mark.parametrize("ma_type", _MA_TYPES)
def test_v2_matches_two_pyta2_ma_batch_calls(ma_type: str) -> None:
    data = _data()
    inner = get_ma_class(ma_type)(5, buffer_size=0)
    outer = get_ma_class(ma_type)(5, buffer_size=0)
    inner_values = get_ma_function(ma_type)(data["close"], 5)
    valid_start = inner.required_window - 1
    outer_values = get_ma_function(ma_type)(inner_values[valid_start:], 5)
    expected = np.concatenate((np.full(valid_start, np.nan), outer_values))

    signal = rKlineMeanOfMeanV2(5, 5, ma_type=ma_type)
    actual = KlineMeanOfMeanV2(data, 5, 5, ma_type=ma_type, return_type="tuple")

    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12, equal_nan=True)
    assert signal.required_window == inner.required_window + outer.required_window - 1
    assert signal.factor_names == [signal.full_name]
    assert signal.full_name.startswith(f"mean_of_mean_v2({inner.full_name},")


def test_sma_v2_matches_v1_but_has_distinct_factor_name() -> None:
    data = _data(20)

    v1 = KlineMeanOfMean(data, 3, 4, return_type="tuple")
    v2 = KlineMeanOfMeanV2(data, 3, 4, ma_type="SMA", return_type="tuple")

    np.testing.assert_allclose(v2, v1, rtol=1e-12, atol=1e-12, equal_nan=True)
    assert rKlineMeanOfMeanV2(3, 4).full_name == (
        "mean_of_mean_v2(SMA(3),SMA(4))[close]"
    )


@pytest.mark.parametrize("ma_type", _MA_TYPES)
def test_repeated_revision_and_next_step_match_finalized_replay(ma_type: str) -> None:
    values = _data(90)["close"]
    signal = rKlineMeanOfMeanV2(5, 5, ma_type=ma_type, buffer_size=2)
    for value in values:
        signal.step(**_bar(float(value)))

    signal.update_last(**_bar(float(values[-1] + 1.0)))
    revised = signal.update_last(**_bar(float(values[-1] + 2.0)))
    assert signal.update_last(**_bar(float(values[-1] + 2.0))) == pytest.approx(revised)
    assert signal.g_index == len(values) - 1
    assert len(signal.outputs) == 2

    continued = signal.step(**_bar(float(values[-1] + 3.0)))
    replay = rKlineMeanOfMeanV2(5, 5, ma_type=ma_type)
    for value in (*values[:-1], values[-1] + 2.0, values[-1] + 3.0):
        expected = replay.step(**_bar(float(value)))

    assert revised == pytest.approx(replay.outputs[-2]["mean_of_mean"])
    assert continued == pytest.approx(expected)
    assert signal._inner.g_index == len(values)
    assert signal._outer.g_index == replay._outer.g_index


@pytest.mark.parametrize("count", [1, 3, 5])
def test_revision_during_each_warmup_stage_matches_replay(count: int) -> None:
    signal = rKlineMeanOfMeanV2(3, 3, ma_type="EMA")
    for value in range(1, count + 1):
        signal.step(**_bar(float(value)))

    revised = signal.update_last(**_bar(10.0))
    replay = rKlineMeanOfMeanV2(3, 3, ma_type="EMA")
    for value in (*range(1, count), 10.0):
        expected = replay.step(**_bar(float(value)))

    if math.isnan(expected):
        assert math.isnan(revised)
    else:
        assert revised == pytest.approx(expected)
    assert signal.step(**_bar(11.0)) == pytest.approx(
        replay.step(**_bar(11.0)), nan_ok=True
    )


def test_kama_advanced_params_field_and_identity() -> None:
    data = _data(80)
    kwargs = {"n2": 3, "n3": 12, "stride": 2}
    signal = rKlineMeanOfMeanV2(5, 6, ma_type="kama", field="volume", ma_kwargs=kwargs)
    actual, meta = KlineMeanOfMeanV2(
        data,
        5,
        6,
        ma_type="kama",
        field="volume",
        ma_kwargs=kwargs,
        return_type="tuple",
        return_meta_info=True,
    )
    inner_values = get_ma_function("KAMA")(data["volume"], 5, 3, 12, 2)
    outer_values = get_ma_function("KAMA")(inner_values[11:], 6, 3, 12, 2)
    expected = np.concatenate((np.full(11, np.nan), outer_values))

    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12, equal_nan=True)
    assert signal.required_window == 23
    assert signal.full_name == (
        "mean_of_mean_v2(KAMA(5,3,12,stride=2),KAMA(6,3,12,stride=2))[volume]"
    )
    assert meta["factor_names"] == [signal.full_name]
    assert meta["ma_type"] == "KAMA"


def test_v2_rejects_overriding_ma_lifecycle_params() -> None:
    with pytest.raises(ValueError, match="must not override"):
        rKlineMeanOfMeanV2(3, 3, ma_kwargs={"buffer_size": 2})
    with pytest.raises(TypeError, match="must be a mapping"):
        rKlineMeanOfMeanV2(3, 3, ma_kwargs=[("n2", 2)])


def test_direct_forward_rejects_lifecycle_outside_step() -> None:
    signal = rKlineMeanOfMeanV2(2, 2)
    values = np.asarray([1.0])

    with pytest.raises(RuntimeError, match=r"requires step\(\) or update_last\(\)"):
        signal.forward(values, values, values, values, values)

    assert signal._inner.g_index == -1
    assert signal._outer.g_index == -1
    assert not signal.is_faulted
    assert math.isnan(signal.step(**_bar(1.0)))


def test_checkpoint_fields_cannot_include_child_indicator() -> None:
    class BadCheckpoint(rKlineMeanOfMeanV2):
        checkpoint_fields = ("_inner",)

    signal = BadCheckpoint(2, 2)
    with pytest.raises(TypeError, match="lifecycle component"):
        signal.step(**_bar(1.0))
