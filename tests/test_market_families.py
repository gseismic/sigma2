from __future__ import annotations

import math

import pytest

from sigma2 import rBookSpread, rTradeSignedVolume


def test_orderbook_signal_uses_snapshot_family_contract():
    signal = rBookSpread(return_dict=True)

    output = signal.step(bids=[(100.0, 2.0)], asks=[(100.5, 3.0)])

    assert output == {"spread": 0.5}
    assert signal.family == "orderbook"
    assert signal.step_input_keys == ("bids", "asks")
    assert signal.latest == {"spread": 0.5}

    with pytest.raises(TypeError):
        signal.step([(100.0, 2.0)], [(100.5, 3.0)])


def test_orderbook_empty_side_returns_nan():
    signal = rBookSpread()

    assert math.isnan(signal.step(bids=[], asks=[(100.5, 3.0)]))
    assert math.isnan(signal.step(bids=[(100.0, 2.0)], asks=[]))


def test_trade_signal_uses_trade_event_family_contract():
    signal = rTradeSignedVolume(return_dict=True)

    assert signal.step(price=10.0, volume=3.0, side="buy") == {"signed_volume": 3.0}
    assert signal.step(price=10.0, volume=3.0, side="sell") == {"signed_volume": -3.0}
    assert signal.step(price=10.0, volume=3.0) == {"signed_volume": 0.0}
    assert signal.family == "trade"
    assert signal.step_input_keys == ("price", "volume", "side")

    with pytest.raises(TypeError):
        signal.step(10.0, 3.0, "buy")


def test_trade_signal_rejects_unknown_side():
    signal = rTradeSignedVolume()

    with pytest.raises(ValueError, match="side must be"):
        signal.step(price=10.0, volume=3.0, side="unknown")
