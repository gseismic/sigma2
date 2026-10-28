"""有限历史输入与 pyta2 Effect 的结果一致。"""

import numpy as np
import pytest
from pyta2.effect import rFutureATRBoundTrigger
from sigma2 import rKlineATRBoundTrigger

def make_data():
    close = np.array([10, 11, 12, 11, 13, 15, 14, 16, 15, 17, 18, 19], dtype=float)
    return {"open": close, "high": close + 1, "low": close - 1,
            "close": close, "volume": np.arange(1, len(close) + 1, dtype=float)}

def test_bound_outcome_matches_full_pyta2_prefix_with_bounded_memory():
    data = make_data()
    data["high"][7] = np.nan
    sigma = rKlineATRBoundTrigger(0.7, 0.8, 3, atr_n=3, atr_ma_type="SMA",
                                  symbol="A", return_dict=True, buffer_size=0)
    pyta = rFutureATRBoundTrigger(0.7, 0.8, 3, n_atr=3, atr_ma_type="SMA",
                                  return_dict=True, buffer_size=0)
    assert sigma.output_keys == pyta.output_keys
    for i in range(len(data["close"])):
        row = {key: values[i] for key, values in data.items()}
        actual = sigma.step(row)
        expected = pyta.rolling(*(data[key][:i + 1] for key in ("open", "high", "low", "close")))
        assert sigma.result_index == pyta.result_index
        for key in sigma.output_keys:
            assert actual[key] == pytest.approx(expected[key], nan_ok=True)
        assert len(sigma._history) <= 4
    sigma.reset()
    assert sigma.result_index == -4
