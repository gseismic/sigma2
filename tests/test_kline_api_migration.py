from __future__ import annotations

import importlib
from collections.abc import Callable
from inspect import signature
from typing import Any

import numpy as np
import pytest

import sigma2
import sigma2.kline as kline
from pyta2 import RSI as PytaRSI
from pyta2 import rRSI as rPytaRSI
from sigma2 import (
    ATR,
    Boll,
    KDJ,
    KlineATR,
    KlineBoll,
    KlineGap,
    KlineKDJ,
    KlineMA,
    KlineMACD,
    KlineRSI,
    KlineReturn,
    MA,
    MACD,
    RSI,
    rATR,
    rBoll,
    rGap,
    rKDJ,
    rKlineATR,
    rKlineBoll,
    rKlineGap,
    rKlineKDJ,
    rKlineMA,
    rKlineMACD,
    rKlineRSI,
    rKlineReturn,
    rMA,
    rMACD,
    rPyta2SMA,
    rReturn,
    rRSI,
    rSMA,
)


def _kline_data(length: int = 32) -> dict[str, np.ndarray]:
    index = np.arange(length, dtype=np.float64)
    close = 100.0 + index * 0.2 + np.sin(index / 3.0)
    open_ = close + np.cos(index / 4.0) * 0.1
    return {
        "open": open_,
        "high": np.maximum(open_, close) + 0.5,
        "low": np.minimum(open_, close) - 0.5,
        "close": close,
        "volume": 1000.0 + index,
    }


def _step_all(signal: Any, data: dict[str, np.ndarray]) -> np.ndarray:
    outputs = []
    for index in range(len(data["close"])):
        outputs.append(
            signal.step(**{key: values[index] for key, values in data.items()})
        )
    return np.asarray(outputs)


def _assert_batch_equal(actual: Any, expected: Any) -> None:
    if isinstance(actual, dict):
        assert actual.keys() == expected.keys()
        for key in actual:
            np.testing.assert_allclose(actual[key], expected[key], equal_nan=True)
        return
    np.testing.assert_allclose(actual, expected, equal_nan=True)


def test_pyta2_and_sigma2_names_can_coexist_without_aliases():
    assert rPytaRSI.__name__ == "rRSI"
    assert PytaRSI.__name__ == "RSI"
    assert rKlineRSI.__name__ == "rKlineRSI"
    assert KlineRSI.__name__ == "KlineRSI"
    assert rPytaRSI is not rKlineRSI
    assert PytaRSI is not KlineRSI


@pytest.mark.parametrize(
    ("old_api", "new_api"),
    [
        (rMA, rKlineMA),
        (rRSI, rKlineRSI),
        (rMACD, rKlineMACD),
        (rBoll, rKlineBoll),
        (rKDJ, rKlineKDJ),
        (rATR, rKlineATR),
        (rReturn, rKlineReturn),
        (rGap, rKlineGap),
        (MA, KlineMA),
        (RSI, KlineRSI),
        (MACD, KlineMACD),
        (Boll, KlineBoll),
        (KDJ, KlineKDJ),
        (ATR, KlineATR),
    ],
)
def test_legacy_short_names_keep_the_replacement_signature(old_api, new_api):
    assert signature(old_api) == signature(new_api)


@pytest.mark.parametrize(
    ("old_cls", "new_cls", "args", "kwargs", "replacement"),
    [
        (rMA, rKlineMA, (5,), {"ma_type": "EMA"}, "rKlineMA"),
        (rRSI, rKlineRSI, (5,), {}, "rKlineRSI"),
        (rMACD, rKlineMACD, (3, 6, 3), {}, "rKlineMACD"),
        (rBoll, rKlineBoll, (5, 2), {}, "rKlineBoll"),
        (rKDJ, rKlineKDJ, (6, 3, 3), {}, "rKlineKDJ"),
        (rATR, rKlineATR, (5,), {}, "rKlineATR"),
        (rReturn, rKlineReturn, (2,), {}, "rKlineReturn"),
        (rGap, rKlineGap, (), {}, "rKlineGap"),
    ],
)
def test_legacy_rolling_names_warn_and_match_canonical(
    old_cls: type,
    new_cls: type,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    replacement: str,
):
    with pytest.warns(DeprecationWarning, match=rf"{replacement}.*0\.4\.0"):
        old = old_cls(*args, **kwargs)
    new = new_cls(*args, **kwargs)

    assert old.full_name == new.full_name
    assert old.factor_names == new.factor_names
    assert old.output_keys == new.output_keys
    np.testing.assert_allclose(
        _step_all(old, _kline_data()),
        _step_all(new, _kline_data()),
        equal_nan=True,
    )


@pytest.mark.parametrize(
    ("old_fn", "new_fn", "args", "kwargs", "replacement"),
    [
        (MA, KlineMA, (5,), {"ma_type": "EMA"}, "KlineMA"),
        (RSI, KlineRSI, (5,), {}, "KlineRSI"),
        (MACD, KlineMACD, (3, 6, 3), {}, "KlineMACD"),
        (Boll, KlineBoll, (5, 2), {}, "KlineBoll"),
        (KDJ, KlineKDJ, (6, 3, 3), {}, "KlineKDJ"),
        (ATR, KlineATR, (5,), {}, "KlineATR"),
    ],
)
def test_legacy_batch_names_warn_and_match_canonical(
    old_fn: Callable[..., Any],
    new_fn: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    replacement: str,
):
    data = _kline_data()
    with pytest.warns(DeprecationWarning, match=rf"{replacement}.*0\.4\.0"):
        old = old_fn(data, *args, **kwargs)
    new = new_fn(data, *args, **kwargs)

    _assert_batch_equal(old, new)


def test_special_legacy_sma_contract_is_preserved_during_migration():
    data = _kline_data(8)
    with pytest.warns(DeprecationWarning, match=r"rKlineMA.*0\.4\.0"):
        old = rSMA(3, field="close", return_dict=True)
    new = rKlineMA(3, ma_type="SMA", field="close", return_dict=True)

    old_outputs = _step_all(old, data)
    new_outputs = _step_all(new, data)

    assert old.output_keys == ["sma"]
    assert old.full_name == "sma(close,3)"
    assert new.output_keys == ["ma"]
    assert new.full_name == "SMA(3)[close]"
    np.testing.assert_allclose(
        [row["sma"] for row in old_outputs.tolist()],
        [row["ma"] for row in new_outputs.tolist()],
        equal_nan=True,
    )


def test_legacy_pyta2_shortcut_warns_and_matches_kline_ma():
    data = _kline_data(8)
    with pytest.warns(DeprecationWarning, match=r"rKlineMA.*0\.4\.0"):
        old = rPyta2SMA(3)
    new = rKlineMA(3, ma_type="SMA")

    assert old.full_name == new.full_name == "SMA(3)[close]"
    np.testing.assert_allclose(
        _step_all(old, data),
        _step_all(new, data),
        equal_nan=True,
    )


@pytest.mark.parametrize(
    ("old_module", "compat_module", "name"),
    [
        ("sigma2.kline.ma", "sigma2.kline.compat.ma", "rMA"),
        ("sigma2.kline.rsi", "sigma2.kline.compat.rsi", "rRSI"),
        ("sigma2.kline.macd", "sigma2.kline.compat.macd", "rMACD"),
        ("sigma2.kline.boll", "sigma2.kline.compat.boll", "rBoll"),
        ("sigma2.kline.kdj", "sigma2.kline.compat.kdj", "rKDJ"),
        ("sigma2.kline.atr", "sigma2.kline.compat.atr", "rATR"),
        ("sigma2.kline.return_", "sigma2.kline.compat.return_", "rReturn"),
        ("sigma2.kline.gap", "sigma2.kline.compat.gap", "rGap"),
        ("sigma2.kline.sma", "sigma2.kline.compat.sma", "rSMA"),
        ("sigma2.kline.pyta2.sma", "sigma2.kline.compat.pyta2_sma", "rPyta2SMA"),
    ],
)
def test_old_module_paths_are_thin_compatibility_forwarders(
    old_module: str,
    compat_module: str,
    name: str,
):
    old_value = getattr(importlib.import_module(old_module), name)
    compat_value = getattr(importlib.import_module(compat_module), name)

    assert old_value is compat_value
    assert old_value.__module__.startswith("sigma2.kline.compat.")


def test_deprecated_names_remain_explicitly_importable_but_are_not_discoverable():
    deprecated = {
        "ATR",
        "Boll",
        "KDJ",
        "MA",
        "MACD",
        "RSI",
        "rATR",
        "rBoll",
        "rGap",
        "rKDJ",
        "rMA",
        "rMACD",
        "rPyta2SMA",
        "rRSI",
        "rReturn",
        "rSMA",
    }

    assert all(hasattr(sigma2, name) for name in deprecated)
    assert all(hasattr(kline, name) for name in deprecated)
    assert deprecated.isdisjoint(sigma2.__all__)
    assert deprecated.isdisjoint(kline.__all__)


def test_price_batch_pairs_match_rolling_replay():
    data = _kline_data(12)

    for batch, rolling, args in (
        (KlineReturn, rKlineReturn, (2,)),
        (KlineGap, rKlineGap, ()),
    ):
        result = batch(data, *args, return_type="tuple")
        replay = _step_all(rolling(*args), data)
        np.testing.assert_allclose(result, replay, equal_nan=True)
