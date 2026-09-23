from __future__ import annotations

from typing import Any

import numpy as np

from pyta2 import RSI as PytaRSI
from pyta2 import rRSI as rPytaRSI
from sigma2 import (
    KlineGap,
    KlineRSI,
    KlineReturn,
    rKlineGap,
    rKlineRSI,
    rKlineReturn,
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


def test_pyta2_and_sigma2_names_can_coexist_without_aliases():
    assert rPytaRSI.__name__ == "rRSI"
    assert PytaRSI.__name__ == "RSI"
    assert rKlineRSI.__name__ == "rKlineRSI"
    assert KlineRSI.__name__ == "KlineRSI"
    assert rPytaRSI is not rKlineRSI
    assert PytaRSI is not KlineRSI


def test_price_batch_pairs_match_rolling_replay():
    data = _kline_data(12)

    for batch, rolling, args in (
        (KlineReturn, rKlineReturn, (2,)),
        (KlineGap, rKlineGap, ()),
    ):
        result = batch(data, *args, return_type="tuple")
        replay = _step_all(rolling(*args), data)
        np.testing.assert_allclose(result, replay, equal_nan=True)
