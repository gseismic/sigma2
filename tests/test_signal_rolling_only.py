from __future__ import annotations

import math

import numpy as np
import pytest
from pyta2 import rSMA as _rPytaSMA
from pyta2.utils.deque import NumpyDeque
from pyta2.utils.space import Scalar

from sigma2 import rPyta2Signal, rSignal
from sigma2.core import rOrderBookSignal
from sigma2.kline import rKlineMA
from sigma2.kline.target import (
    rKlineATRBoundTrigger,
    rKlineFutureChange,
    rKlineFutureHighLowChange,
    rKlineFutureReturn,
)
from sigma2.orderbook import rBookSpread
from sigma2.trade import rTradeSignedVolume


def _kline(value: float) -> dict[str, float]:
    return {
        "open": value,
        "high": value,
        "low": value,
        "close": value,
        "volume": 1.0,
    }


@pytest.mark.parametrize(
    "signal",
    [
        rKlineMA(2),
        rPyta2Signal("SMA", params={"n": 2}),
        rBookSpread(),
        rTradeSignedVolume(),
        rKlineFutureReturn(1),
        rKlineFutureChange(1),
        rKlineFutureHighLowChange(1),
        rKlineATRBoundTrigger(1.0, 1.0, 1, atr_n=1),
    ],
)
def test_signals_do_not_expose_last_observation_revision(signal):
    assert not hasattr(signal, "update_last")
    assert "supports_update_last" not in signal.meta_info
    assert not hasattr(signal, "checkpoint_fields")


def test_kline_and_pyta2_child_advance_together():
    signal = rKlineMA(3, ma_type="SMA", buffer_size=2)
    actual = [signal.step(**_kline(value)) for value in (1.0, 2.0, 3.0, 4.0)]

    assert math.isnan(actual[0])
    assert actual[-2:] == pytest.approx([2.0, 3.0])
    assert signal.g_index == signal._indicator.g_index == 3
    assert len(signal.outputs) == 2
    assert signal._window["close"].tolist() == [2.0, 3.0, 4.0]

    signal.reset()
    replay = [signal.step(**_kline(value)) for value in (1.0, 2.0, 3.0, 4.0)]
    np.testing.assert_allclose(actual, replay, equal_nan=True)


def test_generic_pyta2_bridge_uses_rolling_child():
    signal = rPyta2Signal("SMA", params={"n": 2}, field="close")
    assert math.isnan(signal.step(**_kline(1.0)))
    assert signal.step(**_kline(3.0)) == pytest.approx(2.0)
    assert signal.step(**_kline(5.0)) == pytest.approx(4.0)
    assert signal.g_index == signal._indicator.g_index == 2


def test_orderbook_and_trade_steps_append_new_outputs():
    spread = rBookSpread(return_dict=True)
    assert spread.step(bids=[(100.0, 1.0)], asks=[(101.0, 1.0)]) == {
        "spread": 1.0
    }
    assert spread.step(bids=[(100.25, 1.0)], asks=[(100.75, 1.0)]) == {
        "spread": 0.5
    }
    assert spread.g_index == 1
    assert len(spread.outputs) == 2

    trade = rTradeSignedVolume(return_dict=True)
    assert trade.step(price=10.0, volume=3.0, side="buy") == {
        "signed_volume": 3.0
    }
    assert trade.step(price=10.0, volume=4.0, side="sell") == {
        "signed_volume": -4.0
    }
    assert trade.g_index == 1
    assert len(trade.outputs) == 2


class _rSmoothedDepthImbalance(rOrderBookSignal):
    name = "smoothed_depth_imbalance"

    def __init__(self, n: int = 2, *, levels: int = 1, **kwargs):
        self.n = n
        self.levels = levels
        self._imbalances = NumpyDeque(maxlen=n)
        self._sma = _rPytaSMA(n, buffer_size=0)
        super().__init__(
            window=n,
            schema={
                "smoothed_depth_imbalance": Scalar(
                    low=-1.0, high=1.0, dtype=np.float64
                )
            },
            **kwargs,
        )

    def reset_extras(self):
        self._imbalances.clear()
        self._sma.reset()

    def forward(self, bids, asks):
        bid_depth = sum(size for _, size in bids[: self.levels])
        ask_depth = sum(size for _, size in asks[: self.levels])
        total = bid_depth + ask_depth
        imbalance = math.nan if total <= 0 else (bid_depth - ask_depth) / total
        self._imbalances.append(imbalance)
        return self._sma.rolling(self._imbalances.values)

    @property
    def full_name(self):
        return f"{self.name}(levels={self.levels},n={self.n})"


def test_orderbook_composition_and_child_replay_together():
    rows = [
        {"bids": [(100.0, 3.0)], "asks": [(101.0, 1.0)]},
        {"bids": [(100.0, 1.0)], "asks": [(101.0, 3.0)]},
        {"bids": [(100.0, 5.0)], "asks": [(101.0, 1.0)]},
    ]
    signal = _rSmoothedDepthImbalance()
    actual = [signal.step(**row) for row in rows]
    assert actual[1:] == pytest.approx([0.0, 1.0 / 12.0])
    assert signal.g_index == signal._sma.g_index == 2

    signal.reset()
    replay = [signal.step(**row) for row in rows]
    np.testing.assert_allclose(actual, replay, equal_nan=True)


class _rFailingAccumulator(rSignal):
    name = "failing_accumulator"
    family = "test"
    step_input_keys = ("value",)

    def __init__(self):
        self.total = 0.0
        super().__init__(
            window=1,
            schema={"total": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
        )

    def reset_extras(self):
        self.total = 0.0

    def forward(self, value):
        self.total += value
        if value < 0:
            raise ValueError("negative test input")
        return self.total

    @property
    def full_name(self):
        return str(self.name)


def test_failed_state_calculation_faults_signal_until_reset():
    signal = _rFailingAccumulator()
    signal.step(2.0)

    with pytest.raises(ValueError, match="negative test input"):
        signal.step(-1.0)

    assert signal.is_faulted
    assert signal.g_index == 0
    assert signal.latest == {"total": 2.0}
    with pytest.raises(RuntimeError, match="call reset"):
        signal.step(3.0)

    signal.reset()
    assert not signal.is_faulted
    assert signal.step(2.0) == 2.0
    assert signal.step(3.0) == 5.0
