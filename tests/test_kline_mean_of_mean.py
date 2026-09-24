from __future__ import annotations

import math

import numpy as np
import pytest

from sigma2.kline import KlineMeanOfMean, rKlineMeanOfMean


def _bar(close: float, *, volume: float | None = None) -> dict[str, float]:
    return {
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": close if volume is None else volume,
    }


def _expected(values: list[float], inner_n: int, outer_n: int) -> list[float]:
    result: list[float] = []
    for index in range(len(values)):
        if index + 1 < inner_n + outer_n - 1:
            result.append(float("nan"))
            continue
        inner_means = [
            sum(values[end - inner_n + 1 : end + 1]) / inner_n
            for end in range(index - outer_n + 1, index + 1)
        ]
        result.append(sum(inner_means) / outer_n)
    return result


@pytest.mark.parametrize("inner_n,outer_n", [(1, 1), (1, 3), (3, 1), (2, 3)])
def test_two_stage_mean_matches_independent_formula(inner_n: int, outer_n: int) -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    signal = rKlineMeanOfMean(inner_n, outer_n)

    actual = [signal.step(**_bar(value)) for value in values]

    np.testing.assert_allclose(
        actual, _expected(values, inner_n, outer_n), equal_nan=True
    )
    assert signal.required_window == inner_n + outer_n - 1
    assert signal.output_keys == ["mean_of_mean"]
    assert signal.schema["mean_of_mean"].dtype == np.dtype("float64")


def test_revision_and_continuation_match_finalized_replay() -> None:
    signal = rKlineMeanOfMean(2, 2, return_dict=True, buffer_size=2)
    for value in (1.0, 2.0, 3.0):
        signal.step(**_bar(value))

    assert signal.update_last(**_bar(5.0)) == {"mean_of_mean": pytest.approx(2.5)}
    assert signal.update_last(**_bar(6.0)) == {"mean_of_mean": pytest.approx(2.75)}
    assert signal.update_last(**_bar(6.0)) == {"mean_of_mean": pytest.approx(2.75)}
    assert signal.g_index == 2
    assert len(signal.outputs) == 2
    assert signal.latest == {"mean_of_mean": pytest.approx(2.75)}

    continued = signal.step(**_bar(4.0))
    replay = rKlineMeanOfMean(2, 2, return_dict=True)
    for value in (1.0, 2.0, 6.0, 4.0):
        expected = replay.step(**_bar(value))
    assert continued == expected == {"mean_of_mean": pytest.approx(4.5)}

    signal.reset()
    assert signal.g_index == -1
    assert signal.latest is None
    assert math.isnan(signal.step(**_bar(10.0))["mean_of_mean"])


def test_missing_input_recovers_after_leaving_both_windows() -> None:
    values = [1.0, 2.0, float("nan"), 4.0, 5.0, 6.0, 7.0]
    signal = rKlineMeanOfMean(2, 2)

    actual = [signal.step(**_bar(value)) for value in values]

    np.testing.assert_allclose(actual, _expected(values, 2, 2), equal_nan=True)
    assert actual[5] == pytest.approx(5.0)


def test_batch_uses_field_and_preserves_identity() -> None:
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    data = {key: values for key in ("open", "high", "low", "close")}
    data["volume"] = [1.0, 2.0, 3.0, 4.0, 5.0]

    columns, meta = KlineMeanOfMean(data, 2, 2, field="volume", return_meta_info=True)

    name = "mean_of_mean(2,2)[volume]"
    assert list(columns) == [name]
    np.testing.assert_allclose(
        columns[name], [np.nan, np.nan, 2.0, 3.0, 4.0], equal_nan=True
    )
    assert columns[name].dtype == np.dtype("float64")
    assert meta["factor_names"] == [name]
    assert meta["family"] == "kline"
    assert meta["required_window"] == 3


@pytest.mark.parametrize("bad", [0, -1, 2.5, True])
def test_window_parameters_require_positive_integers(bad: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        rKlineMeanOfMean(bad, 2)


def test_field_must_be_a_standard_kline_field() -> None:
    with pytest.raises(ValueError, match="field must be one of"):
        rKlineMeanOfMean(field="amount")
