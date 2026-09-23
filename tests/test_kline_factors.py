from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pytest
from pyta2.momentum import KDJ as pyta_KDJ
from pyta2.momentum import MACD as pyta_MACD
from pyta2.momentum import RSI as pyta_RSI
from pyta2.stats.atr import ATR as pyta_ATR
from pyta2.structure.channel import Boll as pyta_Boll
from pyta2.trend.ma.api import get_ma_function

from sigma2 import KlineATR, KlineBoll, KlineKDJ, KlineMA, KlineMACD, KlineRSI
from sigma2 import rKlineATR, rKlineBoll, rKlineKDJ, rKlineMA, rKlineMACD, rKlineRSI
from sigma2.core import forward_signal_apply


def _kline_data(length: int = 96) -> dict[str, np.ndarray]:
    index = np.arange(length, dtype=np.float64)
    close = 100.0 + index * 0.08 + np.sin(index / 2.7) * 2.5
    open_ = close + np.cos(index / 4.1) * 0.3
    high = np.maximum(open_, close) + 0.8 + (index % 3) * 0.05
    low = np.minimum(open_, close) - 0.7 - (index % 4) * 0.04
    volume = 1000.0 + index * 7.0 + np.sin(index / 5.0) * 50.0
    return {
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def _as_columns(value: Any) -> tuple[np.ndarray, ...]:
    if isinstance(value, tuple):
        return tuple(np.asarray(column) for column in value)
    return (np.asarray(value),)


def _assert_columns_equal(actual: Any, expected: Any) -> None:
    actual_columns = _as_columns(actual)
    expected_columns = _as_columns(expected)
    assert len(actual_columns) == len(expected_columns)
    for actual_column, expected_column in zip(actual_columns, expected_columns):
        np.testing.assert_allclose(
            actual_column,
            expected_column,
            rtol=1e-12,
            atol=1e-12,
            equal_nan=True,
        )


@pytest.mark.parametrize(
    "ma_type",
    ["SMA", "EMA", "WMA", "HMA", "DEMA", "TEMA", "KAMA", "ZLEMA"],
)
def test_ma_supports_every_public_pyta2_ma_type(ma_type: str):
    data = _kline_data()

    actual = KlineMA(data, 5, ma_type=ma_type, return_type="tuple")
    expected = get_ma_function(ma_type)(data["close"], 5)

    _assert_columns_equal(actual, expected)


def test_ma_field_binding_and_advanced_kwargs_are_part_of_identity():
    data = _kline_data()
    ma_kwargs = {"n2": 3, "n3": 12, "stride": 2}
    signal = rKlineMA(
        5,
        ma_type="kama",
        field="volume",
        ma_kwargs=ma_kwargs,
    )

    actual = KlineMA(
        data,
        5,
        ma_type="kama",
        field="volume",
        ma_kwargs=ma_kwargs,
        return_type="tuple",
    )
    expected = get_ma_function("KAMA")(data["volume"], 5, 3, 12, 2)

    _assert_columns_equal(actual, expected)
    assert signal.full_name == "KAMA(5,3,12,stride=2)[volume]"
    assert signal.factor_names == [signal.full_name]


@pytest.mark.parametrize(
    ("factory", "batch", "pyta_batch"),
    [
        (
            lambda: rKlineMA(5, ma_type="EMA"),
            lambda data: KlineMA(data, 5, ma_type="EMA", return_type="tuple"),
            lambda data: get_ma_function("EMA")(data["close"], 5),
        ),
        (
            lambda: rKlineRSI(5),
            lambda data: KlineRSI(data, 5, return_type="tuple"),
            lambda data: pyta_RSI(data["close"], 5),
        ),
        (
            lambda: rKlineMACD(3, 6, 3),
            lambda data: KlineMACD(
                data,
                fast=3,
                slow=6,
                signal=3,
                return_type="tuple",
            ),
            lambda data: pyta_MACD(data["close"], 3, 6, 3),
        ),
        (
            lambda: rKlineBoll(5, 2),
            lambda data: KlineBoll(data, 5, 2, return_type="tuple"),
            lambda data: pyta_Boll(data["close"], 5, 2),
        ),
        (
            lambda: rKlineKDJ(6, 3, 3),
            lambda data: KlineKDJ(data, 6, 3, 3, return_type="tuple"),
            lambda data: pyta_KDJ(
                data["high"],
                data["low"],
                data["close"],
                6,
                3,
                3,
            ),
        ),
        (
            lambda: rKlineATR(5),
            lambda data: KlineATR(data, 5, return_type="tuple"),
            lambda data: pyta_ATR(
                data["high"],
                data["low"],
                data["close"],
                5,
            ),
        ),
    ],
    ids=["ma", "rsi", "macd", "boll", "kdj", "atr"],
)
def test_factor_batch_matches_signal_replay_and_pyta2(
    factory: Callable[[], Any],
    batch: Callable[[dict[str, np.ndarray]], Any],
    pyta_batch: Callable[[dict[str, np.ndarray]], Any],
):
    data = _kline_data()
    signal = factory()
    replay_values = {key: [] for key in signal.output_keys}
    for index in range(len(data["close"])):
        output = signal.step(**{key: values[index] for key, values in data.items()})
        normalized = signal.make_dict_output(output)
        for key in signal.output_keys:
            replay_values[key].append(normalized[key])

    actual = batch(data)
    replay = tuple(np.asarray(replay_values[key]) for key in signal.output_keys)

    _assert_columns_equal(actual, replay[0] if len(replay) == 1 else replay)
    _assert_columns_equal(actual, pyta_batch(data))


@pytest.mark.parametrize(
    "factory",
    [
        lambda: rKlineMA(5, ma_type="EMA"),
        lambda: rKlineRSI(5),
        lambda: rKlineMACD(3, 6, 3),
        lambda: rKlineBoll(5),
        lambda: rKlineKDJ(6, 3, 3),
        lambda: rKlineATR(5),
    ],
    ids=["ma", "rsi", "macd", "boll", "kdj", "atr"],
)
def test_every_factor_update_last_is_idempotent_and_matches_replay(factory):
    data = _kline_data(24)
    rows = [
        {key: values[index] for key, values in data.items()}
        for index in range(len(data["close"]))
    ]
    signal = factory()
    for row in rows:
        signal.step(**row)

    revised = dict(rows[-1])
    revised["close"] += 1.25
    revised["high"] += 1.5
    first = signal.update_last(**revised)
    second = signal.update_last(**revised)

    replay = factory()
    for row in [*rows[:-1], revised]:
        expected = replay.step(**row)

    _assert_columns_equal(first, second)
    _assert_columns_equal(first, expected)
    assert signal.g_index == replay.g_index == len(rows) - 1
    assert signal._indicator.g_index == replay._indicator.g_index == len(rows) - 1


def test_factor_names_use_full_name_and_output_component():
    ma = rKlineMA(20, ma_type="ema", field="volume")
    macd = rKlineMACD(field="close")
    boll = rKlineBoll()
    atr = rKlineATR(ma_type="ema")

    assert ma.full_name == "EMA(20)[volume]"
    assert ma.factor_names == ["EMA(20)[volume]"]
    assert macd.full_name == "MACD(26,12,9)[close]"
    assert macd.factor_names == [
        "MACD(26,12,9)[close].dif",
        "MACD(26,12,9)[close].dea",
        "MACD(26,12,9)[close].macd",
    ]
    assert boll.full_name == "Boll(20,2)[close]"
    assert atr.full_name == "ATR(20,EMA)[high,low,close]"
    assert atr.meta_info["fields"] == ("high", "low", "close")
    assert atr.meta_info["component"]["full_name"] == "ATR(20,EMA)"


def test_batch_result_formats_and_metadata_use_factor_names():
    data = _kline_data(8)

    as_dict, meta = KlineRSI(data, 3, return_meta_info=True)
    as_tuple = KlineRSI(data, 3, return_type="tuple")
    as_list = KlineRSI(data, 3, return_type="list")

    assert list(as_dict) == ["RSI(3)[close]"]
    np.testing.assert_allclose(
        as_dict["RSI(3)[close]"],
        as_tuple,
        equal_nan=True,
    )
    assert len(as_list) == len(data["close"])
    assert list(as_list[-1]) == ["RSI(3)[close]"]
    assert meta["full_name"] == "RSI(3)[close]"
    assert meta["factor_names"] == ["RSI(3)[close]"]
    assert meta["g_index"] == len(data["close"]) - 1


def test_batch_optional_dataframe_formats():
    pandas = pytest.importorskip("pandas")
    polars = pytest.importorskip("polars")
    data = _kline_data(8)

    pandas_frame = KlineRSI(data, 3, return_type="dataframe")
    polars_frame = KlineRSI(data, 3, return_type="pl.dataframe")

    assert isinstance(pandas_frame, pandas.DataFrame)
    assert isinstance(polars_frame, polars.DataFrame)
    assert list(pandas_frame.columns) == ["RSI(3)[close]"]
    assert polars_frame.columns == ["RSI(3)[close]"]


def test_atr_n_one_keeps_previous_close_for_true_range():
    data = {
        "open": np.asarray([9.5, 14.5, 12.0]),
        "high": np.asarray([10.0, 15.0, 13.0]),
        "low": np.asarray([9.0, 14.0, 11.0]),
        "close": np.asarray([9.5, 14.5, 12.0]),
        "volume": np.ones(3),
    }

    actual = KlineATR(data, 1, return_type="tuple")
    expected = pyta_ATR(data["high"], data["low"], data["close"], 1)

    _assert_columns_equal(actual, expected)
    assert rKlineATR(1).history_window == 2


def test_batch_validates_columnar_contract_and_result_type():
    data = _kline_data(4)

    with pytest.raises(KeyError, match="missing required columns"):
        KlineRSI({key: value for key, value in data.items() if key != "volume"}, 2)

    uneven = dict(data)
    uneven["volume"] = uneven["volume"][:-1]
    with pytest.raises(ValueError, match="same length"):
        KlineRSI(uneven, 2)

    two_dimensional = dict(data)
    two_dimensional["close"] = two_dimensional["close"][:, None]
    with pytest.raises(ValueError, match="one-dimensional"):
        KlineRSI(two_dimensional, 2)

    with pytest.raises(ValueError, match="return_type must be one of"):
        KlineRSI(data, 2, return_type="records")

    with pytest.raises(TypeError, match="rSignal subclass"):
        forward_signal_apply(data, object)


def test_batch_accepts_empty_finalized_table():
    data = {key: values[:0] for key, values in _kline_data(2).items()}

    result, meta = KlineRSI(data, 2, return_meta_info=True)

    assert result["RSI(2)[close]"].shape == (0,)
    assert meta["g_index"] == -1


def test_factor_constructor_validation_is_clear():
    with pytest.raises(ValueError, match="primary window"):
        rKlineMA(5, ma_kwargs={"buffer_size": 10})

    with pytest.raises(TypeError, match="ma_kwargs must be a mapping"):
        rKlineMA(5, ma_kwargs=[("stride", 1)])

    with pytest.raises(ValueError, match="slow must be greater"):
        rKlineMACD(fast=12, slow=12)

    with pytest.raises(ValueError, match="finite number"):
        rKlineBoll(F=float("nan"))

    with pytest.raises(ValueError, match="n1 must be greater"):
        rKlineKDJ(n1=3, n2=3, n3=2)
