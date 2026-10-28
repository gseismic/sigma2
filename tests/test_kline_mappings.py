from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

import numpy as np
import pytest
from pyta2.utils.space import Scalar

from sigma2 import forward_outcome_apply, forward_signal_apply
from sigma2.core import rKlineBundleSignal, rKlineSignal, rPyta2Signal
from sigma2.kline import (
    KlineATR,
    KlineBoll,
    KlineGap,
    KlineKDJ,
    KlineMA,
    KlineMACD,
    KlineMeanOfMean,
    KlineMeanOfMeanV2,
    KlineReturn,
    KlineRSI,
    rKlineATRBoundTrigger,
    rKlineBoll,
    rKlineFutureChange,
    rKlineFutureHighLowChange,
    rKlineFutureReturn,
    rKlineMA,
    rKlineMACD,
    rKlineMeanOfMean,
    rKlineMeanOfMeanV2,
    rKlineRSI,
)
from sigma2.kline_bundle import (
    KlineBundleFutureReturn,
    KlineBundleMA,
    KlineBundleRank,
    KlineBundleReturnRank,
    rKlineBundleMA,
    rKlineBundleMapSignal,
    rKlineBundleRank,
)


def bar(close, **extra):
    return {"open": close, "high": close, "low": close, "close": close, **extra}


class rMappedFields(rKlineSignal):
    def __init__(self, **kwargs):
        super().__init__(
            {"value": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            n_backward=0,
            required_fields=("date", "amount"),
            **kwargs,
        )

    def forward(self, row):
        if row.get("is_missing", False):
            return np.nan
        assert isinstance(row, Mapping)
        self.seen = (row["date"], row["amount"], row.get("extra"))
        return float(row["amount"])

    @property
    def full_name(self):
        return "mapped_fields"


class rMappedBundle(rKlineBundleSignal):
    def __init__(self, *, symbols, **kwargs):
        super().__init__(
            {"total": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            symbols=symbols,
            per_symbol=False,
            n_backward=0,
            required_fields=("amount",),
            required_bundle_fields=("date",),
            **kwargs,
        )

    def forward(self, bundle):
        assert isinstance(bundle, Mapping)
        self.seen = (bundle["date"], bundle["note"], bundle["bundle"]["A"]["extra"])
        return float(np.nansum(bundle.field("amount")))

    @property
    def full_name(self):
        return "mapped_bundle"


def test_single_dictionary_has_optional_metadata_and_snapshots_reused_rows():
    signal = rKlineMA(2)
    row = bar(10, unrelated={"value": 1})
    assert np.isnan(signal.step(row))
    row.update(bar(20))
    assert signal.step(row) == pytest.approx(15)
    assert signal.n_backward == 1 and signal.min_periods == 2
    assert signal.meta_info["last_bar_time"] is None
    assert signal.meta_info["symbol"] is None


@pytest.mark.parametrize("field", ["open", "high", "low", "close"])
def test_missing_base_field_fails_before_advancing(field):
    signal = rKlineMA(2)
    row = bar(10)
    row.pop(field)
    with pytest.raises(KeyError, match=field):
        signal.step(row)
    assert signal.g_index == -1 and not signal.is_faulted
    assert np.isnan(signal.step(bar(10)))


@pytest.mark.parametrize(
    "factory",
    [
        lambda: rKlineMA(2, field="volume"),
        lambda: rKlineRSI(2, field="volume"),
        lambda: rKlineMACD(2, 3, 2, field="volume"),
        lambda: rKlineBoll(2, field="volume"),
        lambda: rKlineMeanOfMean(2, 2, field="volume"),
        lambda: rKlineMeanOfMeanV2(2, 2, field="volume"),
        lambda: rKlineFutureReturn(1, field="volume"),
        lambda: rKlineFutureChange(1, field="volume"),
        lambda: rKlineFutureHighLowChange(1, reference_field="volume"),
        lambda: rPyta2Signal("SMA", history_window=2, params={"n": 2}, field="volume"),
    ],
)
def test_volume_is_required_only_for_algorithms_that_use_it(factory):
    signal = factory()
    with pytest.raises(KeyError, match="volume"):
        signal.step(bar(10))
    assert signal.g_index == -1 and not signal.is_faulted
    signal.step(bar(10, volume=5))
    assert signal.g_index == 0


def test_mapping_is_logical_to_source_preserves_extras_and_configuration():
    key_map = {"date": "open_time", "amount": "turnover"}
    signal = rMappedFields(key_map=key_map)
    key_map["date"] = "another_time"
    row = bar(10, date=-1, open_time=123, amount=99, turnover=7, extra="keep")
    original = dict(row)
    assert signal.step(MappingProxyType(row)) == 7
    assert signal.seen == (123, 7, "keep")
    assert row == original
    assert signal.key_map == {"date": "open_time", "amount": "turnover"}
    leaked = signal.key_map
    leaked["date"] = "date"
    assert signal.meta_info["key_map"]["date"] == "open_time"
    missing = bar(10, date=123, turnover=7)
    with pytest.raises(KeyError, match="date"):
        signal.step(missing)
    assert signal.g_index == 0 and not signal.is_faulted
    with pytest.raises(AttributeError):
        signal.required_fields = ("close",)
    batch = forward_signal_apply(
        [row],
        rMappedFields,
        key_map={"date": "open_time", "amount": "turnover"},
        return_type="tuple",
    )
    np.testing.assert_allclose(batch, [7])


def test_mapping_does_not_chain_or_change_unmapped_optional_fields():
    class rOpenHigh(rKlineSignal):
        def __init__(self, **kwargs):
            super().__init__(
                {"value": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
                n_backward=0,
                **kwargs,
            )

        def forward(self, row):
            return row["open"] * 10 + row["high"]

        @property
        def full_name(self):
            return "open_high"

    row = {"open": 1, "high": 2, "low": 0, "close": 1}
    signal = rOpenHigh(key_map={"open": "high", "high": "open"})
    assert signal.step(row) == 21
    assert row["open"] == 1 and row["high"] == 2
    optional = rKlineMA(1, key_map={"date": "open_time", "volume": "qty"})
    assert optional.step(row) == 1


@pytest.mark.parametrize(
    "key_map", [[("date", "open_time")], {"": "date"}, {"date": ""}]
)
def test_invalid_mapping_configuration_is_rejected(key_map):
    with pytest.raises((TypeError, ValueError), match="key_map"):
        rKlineMA(1, key_map=key_map)


def test_unrelated_uncopyable_extra_field_does_not_reject_a_row():
    class Uncopyable:
        def __deepcopy__(self, memo):
            raise RuntimeError("must not copy unrelated field")

    assert rKlineMA(1).step(bar(10, extra=Uncopyable())) == 10


def test_invalid_optional_volume_does_not_break_close_based_windows():
    assert rKlineMA(1).step(bar(10, volume={"unexpected": 1})) == 10
    assert rKlineMA(1).step(bar(10, volume=[1, 2])) == 10
    bundle = {"bundle": {"A": bar(10, volume={"unexpected": 1})}}
    np.testing.assert_allclose(rKlineBundleMA(1, symbols=("A",)).step(bundle), [10])
    from sigma2.kline_bundle import rKlineBundleReturnRank

    signal = rKlineBundleReturnRank(1, symbols=("A",))
    assert np.isnan(signal.step(bundle)).all()
    np.testing.assert_allclose(signal.step(bundle), [1])


def test_explicit_symbol_checks_present_value_but_does_not_require_it():
    signal = rKlineMA(1, symbol="A")
    assert signal.step(bar(10)) == 10
    with pytest.raises(ValueError, match="symbol"):
        signal.step(bar(20, symbol="B"))
    assert signal.g_index == 0 and not signal.is_faulted
    assert signal.step(bar(20, symbol="A")) == 20


def test_single_batch_columnar_and_rows_match_with_mapped_metadata():
    rows = [bar(10, open_time=100), bar(20, open_time=200)]
    columns = {key: [row[key] for row in rows] for key in rows[0]}
    params = {"bar_time": "open_time"}
    row_result, meta = KlineMA(rows, 2, key_map=params, return_meta_info=True)
    col_result = KlineMA(columns, 2, key_map=params, return_type="tuple")
    np.testing.assert_allclose(
        next(iter(row_result.values())), col_result, equal_nan=True
    )
    np.testing.assert_allclose(col_result, [np.nan, 15], equal_nan=True)
    assert meta["bar_times"] == (100, 200)
    assert meta["input_available_at"] == (None, None)
    assert meta["key_map"] == params


@pytest.mark.parametrize(
    ("batch", "args"),
    [
        (KlineMA, (2,)),
        (KlineMACD, (2, 3, 2)),
        (KlineRSI, (2,)),
        (KlineBoll, (2,)),
        (KlineKDJ, (9, 3, 3)),
        (KlineATR, (2,)),
        (KlineGap, ()),
        (KlineReturn, (1,)),
        (KlineMeanOfMean, (2, 2)),
        (KlineMeanOfMeanV2, (2, 2)),
    ],
)
def test_all_single_batch_wrappers_accept_mapping_configuration(batch, args):
    rows = [
        bar(value, source_time=index) for index, value in enumerate((10, 11, 12, 13))
    ]
    _, meta = batch(
        rows, *args, key_map={"bar_time": "source_time"}, return_meta_info=True
    )
    assert meta["bar_times"] == (0, 1, 2, 3)
    assert meta["key_map"] == {"bar_time": "source_time"}


def test_single_outcome_batch_aligns_without_inventing_availability():
    rows = [bar(10, open_time=100), bar(15, open_time=200)]
    result, meta = forward_outcome_apply(
        rows,
        rKlineFutureReturn,
        param_args=(1,),
        key_map={"bar_time": "open_time"},
        return_meta_info=True,
    )
    np.testing.assert_allclose(
        next(iter(result.values())), [0.5, np.nan], equal_nan=True
    )
    assert meta["bar_times"] == (100, 200)
    assert meta["emission_bar_times"] == (200, None)
    assert meta["result_input_ready_at"] == (None, None)


def test_unusable_optional_availability_does_not_break_batch():
    class Uncomparable:
        def __ne__(self, other):
            raise RuntimeError("not comparable")

    rows = [bar(10, available_at=Uncomparable()), bar(15, available_at=2)]
    result, meta = KlineMA(rows, 2, return_meta_info=True)
    np.testing.assert_allclose(
        next(iter(result.values())), [np.nan, 12.5], equal_nan=True
    )
    assert meta["result_input_ready_at"] == (None, None)


def test_outcome_child_uses_the_same_mapped_input_as_its_parent():
    mapped = rKlineATRBoundTrigger(
        0.05, 0.02, 1, atr_n=1, return_dict=True, key_map={"close": "adjusted"}
    )
    plain = rKlineATRBoundTrigger(0.05, 0.02, 1, atr_n=1, return_dict=True)
    rows = [
        {"open": 100, "high": 104, "low": 100, "close": -1, "adjusted": 101},
        {"open": 101, "high": 102, "low": 99, "close": -1, "adjusted": 100},
    ]
    for row in rows:
        actual = mapped.step(row)
        expected = plain.step({**row, "close": row["adjusted"]})
        assert actual["trigger"] == expected["trigger"]
        assert actual["trigger_location"] == expected["trigger_location"]
        np.testing.assert_allclose(
            actual["unit_change"], expected["unit_change"], equal_nan=True
        )


def test_mapping_input_time_order_is_a_caller_responsibility():
    signal = rKlineMA(1)
    assert signal.step(bar(10, bar_time=2)) == 10
    assert signal.step(bar(20, bar_time=1)) == 20
    assert signal.meta_info["last_bar_time"] == 1


def test_dataframe_uses_observation_index_if_times_are_incomplete():
    pd = pytest.importorskip("pandas")
    rows = [bar(10, bar_time=100), bar(20)]
    frame, meta = KlineMA(rows, 2, return_type="dataframe", return_meta_info=True)
    assert isinstance(frame, pd.DataFrame)
    assert frame.index.name == "g_index" and frame.index.tolist() == [0, 1]
    assert meta["bar_times"] == (100, None)
    columnar = pd.DataFrame([bar(10), bar(20)])
    np.testing.assert_allclose(
        KlineMA(columnar, 2, return_type="tuple"), [np.nan, 15], equal_nan=True
    )
    columnar["bar_time"] = pd.Series([100, pd.NA], dtype="object")
    mixed = KlineMA(columnar, 2, return_type="dataframe")
    assert mixed.index.name == "g_index" and mixed.index.tolist() == [0, 1]


def test_bundle_mapping_rank_ma_outcome_and_missing_symbol_share_one_axis():
    symbols = ("A", "B")
    bundles = [
        {"bundle": {"A": bar(10), "B": bar(20)}},
        {"bundle": {"A": bar(12)}},
        {"bundle": {"A": bar(15), "B": bar(30)}},
    ]
    rank = rKlineBundleRank(symbols=symbols)
    np.testing.assert_allclose(rank.step(bundles[0]), [1, 2])
    np.testing.assert_allclose(rank.step(bundles[1]), [1, np.nan], equal_nan=True)
    ma = rKlineBundleMA(2, symbols=symbols)
    replay = np.asarray([ma.step(item) for item in bundles])
    expected = [[np.nan, np.nan], [11, np.nan], [13.5, np.nan]]
    np.testing.assert_allclose(replay, expected, equal_nan=True)
    np.testing.assert_allclose(
        KlineBundleMA(bundles, 2, symbols=symbols, return_type="tuple"),
        expected,
        equal_nan=True,
    )
    result = KlineBundleFutureReturn(bundles, 1, symbols=symbols, return_type="tuple")
    np.testing.assert_allclose(
        result, [[0.2, np.nan], [0.25, np.nan], [np.nan, np.nan]], equal_nan=True
    )


@pytest.mark.parametrize(
    ("batch", "args"),
    [
        (KlineBundleRank, ()),
        (KlineBundleReturnRank, (1,)),
        (KlineBundleMA, (2,)),
        (KlineBundleFutureReturn, (1,)),
    ],
)
def test_all_bundle_batch_wrappers_accept_both_mapping_scopes(batch, args):
    rows = [
        {"source_time": index, "klines": {"A": bar(value, qty=value)}}
        for index, value in enumerate((10, 11, 12))
    ]
    _, meta = batch(
        rows,
        *args,
        symbols=("A",),
        field="volume",
        key_map={"volume": "qty"},
        bundle_key_map={"bundle": "klines", "open_time": "source_time"},
        return_meta_info=True,
    )
    assert meta["bar_times"] == (0, 1, 2)
    assert meta["key_map"] == {"volume": "qty"}
    assert meta["bundle_key_map"] == {"bundle": "klines", "open_time": "source_time"}


def test_bundle_declared_fields_are_checked_before_parent_or_child_advance():
    signal = rKlineBundleMA(2, symbols=("A", "B"), field="volume")
    bad = {"bundle": {"A": bar(1, volume=5), "B": bar(2)}}
    with pytest.raises(KeyError, match="volume"):
        signal.step(bad)
    assert signal.g_index == -1 and not signal.is_faulted
    assert all(child.g_index == -1 for child in signal._operators)
    good = {"bundle": {"A": bar(1, volume=5), "B": bar(2, volume=6)}}
    signal.step(good)
    assert signal.g_index == 0
    assert all(child.g_index == 0 for child in signal._operators)


def test_bundle_custom_fields_and_top_level_mapping_are_available():
    signal = rMappedBundle(
        symbols=("A", "B"),
        key_map={"amount": "turnover"},
        bundle_key_map={"date": "open_time", "bundle": "klines"},
    )
    bundle = {
        "klines": {"A": bar(1, turnover=9, extra="bar-extra")},
        "open_time": 123,
        "note": "bundle-extra",
    }
    assert signal.step(bundle) == 9
    assert signal.seen == (123, "bundle-extra", "bar-extra")
    missing_time = {"klines": bundle["klines"], "note": "x"}
    with pytest.raises(KeyError, match="date"):
        signal.step(missing_time)
    assert signal.g_index == 0 and not signal.is_faulted


def test_bundle_mapping_applies_once_through_single_symbol_children():
    signal = rKlineBundleMA(
        1,
        symbols=("A",),
        key_map={"close": "alternate", "alternate": "another"},
    )
    bundle = {"bundle": {"A": bar(1, alternate=7, another=20)}}
    np.testing.assert_allclose(signal.step(bundle), [7])
    batch = KlineBundleMA(
        [bundle],
        1,
        symbols=("A",),
        return_type="tuple",
        key_map={"close": "alternate", "alternate": "another"},
    )
    np.testing.assert_allclose(batch, [[7]])


def test_bundle_mapping_custom_child_receives_extra_and_missing_placeholders():
    signal = rKlineBundleMapSignal(
        rMappedFields,
        symbols=("A", "B"),
        key_map={"date": "open_time", "amount": "turnover"},
    )
    bundle = {"bundle": {"A": bar(1, open_time=100, turnover=9, extra="x")}}
    np.testing.assert_allclose(signal.step(bundle), [9, np.nan], equal_nan=True)
    assert all(child.g_index == 0 for child in signal._operators)


def test_bundle_missing_placeholders_are_mapping_views_for_custom_children():
    class rClose(rKlineSignal):
        def __init__(self, **kwargs):
            super().__init__(
                {"close": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
                n_backward=0,
                **kwargs,
            )

        def forward(self, row):
            assert isinstance(row, Mapping)
            return row["close"]

        @property
        def full_name(self):
            return "close"

    signal = rKlineBundleMapSignal(rClose, symbols=("A", "B"))
    bundle = {"bundle": {"A": bar(1)}}
    np.testing.assert_allclose(signal.step(bundle), [1, np.nan], equal_nan=True)


def test_bundle_universe_is_explicit_and_unknown_symbols_fail():
    sparse = {"bundle": {"A": bar(1)}}
    with pytest.raises(ValueError, match="symbols must be supplied"):
        KlineBundleRank([sparse])
    with pytest.raises(ValueError, match="unknown"):
        KlineBundleRank([sparse], symbols=("B",))
    mismatch = {"bundle": {"A": bar(1, symbol="B")}}
    signal = rKlineBundleRank(symbols=("A",))
    with pytest.raises(ValueError, match="symbol"):
        signal.step(mismatch)
    assert signal.g_index == -1 and not signal.is_faulted
    with_universe = {**sparse, "symbols": ("A", "B")}
    np.testing.assert_allclose(
        KlineBundleRank([with_universe], return_type="tuple"),
        [[1, np.nan]],
        equal_nan=True,
    )


def test_bundle_batch_mapping_metadata_and_index_fallback():
    pd = pytest.importorskip("pandas")
    bundles = [
        {"bundle": {"A": bar(1)}, "open_time": 10},
        {"bundle": {"A": bar(2)}},
    ]
    frame, meta = KlineBundleRank(
        bundles,
        symbols=("A",),
        return_type="dataframe",
        return_meta_info=True,
    )
    assert isinstance(frame.index, pd.MultiIndex)
    assert frame.index.names == ["g_index", "symbol"]
    assert meta["bar_times"] == (10, None)
    assert meta["bundle_key_map"] == {}


def test_polars_columnar_input_and_missing_time_output():
    pl = pytest.importorskip("polars")
    frame = pl.DataFrame([bar(1), bar(2)])
    result = KlineMA(frame, 1, return_type="pl.dataframe")
    assert result.columns == ["g_index", "SMA(1)[close]"]
    assert result["g_index"].to_list() == [0, 1]
    np.testing.assert_allclose(result["SMA(1)[close]"].to_numpy(), [1, 2])


def test_polars_rejects_factor_names_that_collide_with_index_columns():
    pytest.importorskip("polars")

    class rIndexName(rKlineSignal):
        def __init__(self, **kwargs):
            super().__init__(
                {"value": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
                n_backward=0,
                **kwargs,
            )

        def forward(self, row):
            return row["close"]

        @property
        def full_name(self):
            return "g_index"

    with pytest.raises(ValueError, match="conflict"):
        forward_signal_apply([bar(1)], rIndexName, return_type="pl.dataframe")


def test_batch_mapping_conflicts_and_bad_columns_fail_clearly():
    with pytest.raises(ValueError, match="conflicts"):
        forward_signal_apply(
            [bar(1)],
            rKlineMA,
            param_args=(1,),
            param_kwargs={"key_map": {"date": "a"}},
            key_map={"date": "b"},
        )
    with pytest.raises(ValueError, match="same length"):
        KlineMA({"open": [1], "high": [1], "low": [1], "close": [1, 2]}, 1)
    with pytest.raises(ValueError, match="time dimension"):
        KlineMA(bar(1), 1)
    columns = {"open": [1, 2], "high": [1, 2], "low": [1, 2], "close": [1, 2]}
    columns["extra"] = [[1], [1, 2]]
    np.testing.assert_allclose(KlineMA(columns, 1, return_type="tuple"), [1, 2])
