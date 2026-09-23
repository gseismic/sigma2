from __future__ import annotations

import math

import numpy as np
import pytest
from pyta2 import rSMA as _rPytaSMA
from pyta2.utils.deque import NumpyDeque
from pyta2.utils.space import Scalar

from sigma2 import rPyta2Signal, rSignal
from sigma2.kline import rKlineMA
from sigma2.kline.target import (
    rKlineATRBoundTrigger,
    rKlineFutureChange,
    rKlineFutureHighLowChange,
    rKlineFutureReturn,
)
from sigma2.orderbook import rBookSpread
from sigma2.trade import rTradeSignedVolume
from sigma2.core import rOrderBookSignal


def _kline(value: float) -> dict[str, float]:
    return {
        "open": value,
        "high": value,
        "low": value,
        "close": value,
        "volume": 1.0,
    }


def test_kline_update_last_is_idempotent_and_matches_finalized_replay():
    signal = rKlineMA(3, ma_type="SMA")
    for value in (1.0, 2.0, 3.0):
        signal.step(**_kline(value))

    first = signal.update_last(**_kline(30.0))
    second = signal.update_last(**_kline(30.0))

    assert first == second == pytest.approx(11.0)
    assert signal.g_index == 2
    assert len(signal.outputs) == 3
    assert signal.latest == {"ma": pytest.approx(11.0)}
    assert signal._window["close"].tolist() == [1.0, 2.0, 30.0]

    continued = signal.step(**_kline(4.0))
    replay = rKlineMA(3, ma_type="SMA")
    for value in (1.0, 2.0, 30.0, 4.0):
        expected = replay.step(**_kline(value))

    assert continued == expected == pytest.approx(12.0)


def test_update_last_requires_a_committed_observation_again_after_reset():
    signal = rKlineMA(2, ma_type="SMA")

    with pytest.raises(IndexError, match="requires a preceding step"):
        signal.update_last(**_kline(1.0))

    signal.step(**_kline(1.0))
    signal.reset()

    with pytest.raises(IndexError, match="requires a preceding step"):
        signal.update_last(**_kline(2.0))


def test_pyta2_adapter_routes_update_last_to_child_indicator():
    signal = rPyta2Signal("SMA", params={"n": 2}, field="close")
    signal.step(**_kline(1.0))
    signal.step(**_kline(3.0))

    output = signal.update_last(**_kline(5.0))

    assert output == pytest.approx(3.0)
    assert signal.g_index == 1
    assert signal._indicator.g_index == 1
    assert signal.latest == {"ma": pytest.approx(3.0)}


def test_orderbook_and_trade_families_offer_same_signature_revision():
    spread = rBookSpread(return_dict=True)
    spread.step(bids=[(100.0, 1.0)], asks=[(101.0, 1.0)])

    assert spread.update_last(
        bids=[(100.25, 1.0)],
        asks=[(100.75, 1.0)],
    ) == {"spread": 0.5}
    assert spread.g_index == 0
    assert len(spread.outputs) == 1

    trade = rTradeSignedVolume(return_dict=True)
    trade.step(price=10.0, volume=3.0, side="buy")

    assert trade.update_last(price=10.0, volume=4.0, side="sell") == {
        "signed_volume": -4.0
    }
    assert trade.g_index == 0
    assert len(trade.outputs) == 1


class _rSmoothedDepthImbalance(rOrderBookSignal):
    """设计稿 orderbook 组合指标的最小可执行版本。"""

    name = "smoothed_depth_imbalance"
    _update_state_fields = ("_imbalances",)

    def __init__(self, n: int = 2, *, levels: int = 1, **kwargs):
        self.n = n
        self.levels = levels
        self._imbalances = NumpyDeque(maxlen=n)
        self._sma = _rPytaSMA(n, buffer_size=0)
        super().__init__(
            window=n,
            schema={
                "smoothed_depth_imbalance": Scalar(
                    low=-1.0,
                    high=1.0,
                    dtype=np.float64,
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
        return self._apply_pyta2(self._sma, self._imbalances.values)

    @property
    def full_name(self):
        return f"{self.name}(levels={self.levels},n={self.n})"


def test_orderbook_composition_checkpoint_and_child_revision_match_replay():
    first = {"bids": [(100.0, 3.0)], "asks": [(101.0, 1.0)]}
    old_last = {"bids": [(100.0, 1.0)], "asks": [(101.0, 3.0)]}
    revised_last = {"bids": [(100.0, 5.0)], "asks": [(101.0, 1.0)]}

    signal = _rSmoothedDepthImbalance()
    signal.step(**first)
    signal.step(**old_last)
    revised = signal.update_last(**revised_last)

    replay = _rSmoothedDepthImbalance()
    replay.step(**first)
    expected = replay.step(**revised_last)

    assert revised == pytest.approx(expected)
    assert signal.update_last(**revised_last) == pytest.approx(expected)
    assert signal.g_index == replay.g_index == 1
    assert signal._sma.g_index == replay._sma.g_index == 1


@pytest.mark.parametrize(
    "target",
    [
        rKlineFutureReturn(1),
        rKlineFutureChange(1),
        rKlineFutureHighLowChange(1),
        rKlineATRBoundTrigger(1.0, 1.0, 1, atr_n=1),
    ],
    ids=["return", "change", "high-low", "atr-bound-trigger"],
)
def test_future_effects_reject_current_bar_revision_semantics(target):
    target.step(**_kline(1.0))

    with pytest.raises(NotImplementedError, match="does not support update_last"):
        target.update_last(**_kline(2.0))


class _rFailingAccumulator(rSignal):
    name = "failing_accumulator"
    family = "test"
    step_input_keys = ("value",)
    _update_state_fields = ("total",)

    def __init__(self):
        self.total = 0.0
        super().__init__(
            window=1,
            schema={
                "total": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)
            },
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
    assert signal.step(3.0) == 3.0
