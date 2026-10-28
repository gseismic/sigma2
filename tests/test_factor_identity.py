"""作用域、公式名和 schema 输出键互不混淆。"""

import numpy as np
import pytest

from sigma2 import (
    KlineBundleFutureReturn,
    KlineBundleMA,
    KlineBundleRank,
    KlineBundleReturnRank,
    KlineRSI,
    qualify_factor_name,
    rKlineBundleRank,
    rKlineMACD,
    rKlineRSI,
    rTradeSignedVolume,
)


def bar(close):
    return {"open": close, "high": close + 1, "low": close - 1, "close": close}


def test_single_identity_stable_and_schema_unchanged():
    signal = rKlineRSI(2, symbol="BTC:USDT", return_dict=True)
    assert signal.full_name == "RSI(2)[close]"
    assert signal.formula_names == ["RSI(2)[close]"]
    assert signal.factor_names == ["BTC:USDT:RSI(2)[close]"]
    for close in (10, 11, 12):
        result = signal.step(bar(close))
        assert list(result) == ["rsi"]
        assert signal.factor_names == ["BTC:USDT:RSI(2)[close]"]
    assert signal.meta_info["scope"] == "BTC:USDT"
    signal.reset()
    assert signal.factor_names == ["BTC:USDT:RSI(2)[close]"]
    assert rKlineRSI(2).factor_names == ["RSI(2)[close]"]
    with pytest.raises(AttributeError):
        signal.scope = "ETH"
    with pytest.raises(ValueError):
        rKlineRSI(2, symbol="")


def test_multi_output_and_batch_names():
    signal = rKlineMACD(2, 4, 2, symbol="BTC")
    assert signal.factor_names == ["BTC:" + name for name in signal.formula_names]
    assert len(signal.factor_names) == len(signal.output_keys) == 3
    result = KlineRSI([bar(10), bar(11), bar(12)], 2, symbol="BTC")
    assert list(result) == ["BTC:RSI(2)[close]"]
    np.testing.assert_allclose(result["BTC:RSI(2)[close]"], [np.nan, np.nan, 100], equal_nan=True)


def test_bundle_scope_and_axes_for_all_convenience_apis():
    bundles = [
        {"symbols": ("A", "B"), "bundle": {"A": bar(10), "B": bar(20)}},
        {"symbols": ("A", "B"), "bundle": {"A": bar(12), "B": bar(18)}},
    ]
    rank = rKlineBundleRank(symbols=("A", "B"))
    assert rank.factor_names == ["all:" + rank.full_name]
    assert rank.step(bundles[0]).shape == (2,)
    custom = KlineBundleRank(bundles, scope="top100")
    assert list(custom) == ["top100:" + rank.full_name]
    assert next(iter(custom.values())).shape == (2, 2)
    for result in (
        KlineBundleMA(bundles, 1, scope="top100"),
        KlineBundleReturnRank(bundles, 1, scope="top100"),
        KlineBundleFutureReturn(bundles, 1, scope="top100"),
    ):
        assert len(result) == 1
        name, values = next(iter(result.items()))
        assert name.startswith("top100:")
        assert values.shape == (2, 2)


def test_generic_scope_and_validation():
    assert rTradeSignedVolume(scope="exchange").factor_names == ["exchange:trade_signed_volume"]
    assert qualify_factor_name(None, "SMA(5)[close]") == "SMA(5)[close]"
    assert qualify_factor_name("BTC:USDT", "SMA(5)[close]") == "BTC:USDT:SMA(5)[close]"
    with pytest.raises(ValueError):
        rKlineBundleRank(symbols=("A",), scope="")
    with pytest.raises(ValueError):
        qualify_factor_name("BTC", "")
