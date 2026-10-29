from __future__ import annotations

from types import MappingProxyType

import numpy as np
import pytest
from pyta2.utils.space import Scalar

from sigma2.kline import rKlineSignal
from sigma2.kline_bundle import rKlineBundleSignal
from sigma2.kline_bundle import (
    KlineBundleFutureReturn,
    KlineBundleRank,
    rKlineBundleMapSignal,
    rKlineBundleRank,
)


def bar(close, **extra):
    return {"open": close, "high": close, "low": close, "close": close, **extra}


class rInspectSnapshot(rKlineBundleSignal):
    def __init__(self, **kwargs):
        super().__init__(
            {"value": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            n_backward=0,
            per_symbol=False,
            **kwargs,
        )

    def forward(self, snapshot):
        self.seen = snapshot
        return float(snapshot["bundle"]["A"]["close"])

    @property
    def full_name(self):
        return "inspect_snapshot"


def test_default_snapshot_step_batch_and_outcome_use_open_time():
    snapshots = [
        {"open_time": 10, "bundle": {"A": bar(10), "B": bar(20)}},
        {"open_time": 20, "bundle": {"A": bar(15), "B": bar(30)}},
    ]
    rank = rKlineBundleRank(symbols=("A", "B"))
    np.testing.assert_allclose(rank.step(snapshots[0]), [1, 2])
    assert rank.meta_info["last_bar_time"] == 10
    assert rank.meta_info["required_bundle_fields"] == ("bundle",)
    values, meta = KlineBundleFutureReturn(
        snapshots, 1, symbols=("A", "B"), return_type="tuple", return_meta_info=True
    )
    np.testing.assert_allclose(values, [[0.5, 0.5], [np.nan, np.nan]], equal_nan=True)
    assert meta["bar_times"] == (10, 20)
    assert meta["emission_bar_times"] == (20, None)
    assert meta["input_available_at"] == (None, None)
    assert meta["result_input_ready_at"] == (None, None)


def test_snapshot_accepts_read_only_mappings_at_every_level():
    snapshot = MappingProxyType(
        {
            "open_time": 10,
            "bundle": MappingProxyType({"A": MappingProxyType(bar(10))}),
        }
    )
    signal = rKlineBundleRank(symbols=("A",))
    np.testing.assert_allclose(signal.step(snapshot), [1])
    assert signal.meta_info["last_bar_time"] == 10


def test_default_snapshot_pandas_and_polars_indices_use_open_time():
    pytest.importorskip("pandas")
    pytest.importorskip("polars")
    snapshots = [
        {"open_time": 10, "bundle": {"A": bar(10)}},
        {"open_time": 20, "bundle": {"A": bar(20)}},
    ]
    frame = KlineBundleRank(snapshots, symbols=("A",), return_type="dataframe")
    assert frame.index.names == ["bar_time", "symbol"]
    assert frame.index.tolist() == [(10, "A"), (20, "A")]
    frame = KlineBundleRank(snapshots, symbols=("A",), return_type="pl.dataframe")
    assert frame["bar_time"].to_list() == [10, 20]
    assert frame["symbol"].to_list() == ["A", "A"]


def test_empty_snapshot_time_and_available_at_are_independent():
    snapshots = [
        {"open_time": 10, "available_at": 11, "bundle": {"A": bar(10)}},
        {"available_at": 21, "bundle": {}},
    ]
    values, meta = KlineBundleRank(
        snapshots, symbols=("A",), return_type="tuple", return_meta_info=True
    )
    np.testing.assert_allclose(values, [[1], [np.nan]], equal_nan=True)
    assert meta["bar_times"] == (10, None)
    assert meta["input_available_at"] == (11, 21)
    assert meta["result_input_ready_at"] == (11, 21)


def test_new_mapping_applies_once_and_preserves_unrelated_bars_field():
    signal = rInspectSnapshot(
        symbols=("A",),
        key_map={"close": "adjusted"},
        bundle_key_map={"bundle": "klines", "open_time": "date"},
    )
    snapshot = {
        "klines": {"A": bar(1, adjusted=7)},
        "bundle": {"A": bar(99)},
        "date": 123,
        "open_time": 456,
        "bars": "额外字段",
    }
    assert signal.step(snapshot) == 7
    assert signal.seen["bundle"]["A"]["close"] == 7
    assert signal.seen.bars == "额外字段"
    assert signal.seen["bars"] == "额外字段"
    assert signal.seen["open_time"] == 123
    assert signal.meta_info["last_bar_time"] == 123
    assert snapshot["bundle"]["A"]["close"] == 99


def test_batch_reads_mapped_symbol_universe_and_snapshot_fields():
    snapshot = {"universe": ("A", "B"), "klines": {"A": bar(1)}, "date": 10}
    values, meta = KlineBundleRank(
        [snapshot],
        bundle_key_map={"symbols": "universe", "bundle": "klines", "open_time": "date"},
        return_type="tuple",
        return_meta_info=True,
    )
    np.testing.assert_allclose(values, [[1, np.nan]], equal_nan=True)
    assert meta["symbols"] == ("A", "B") and meta["bar_times"] == (10,)


def test_required_bars_extra_is_snapshotted_when_it_is_not_the_bundle():
    signal = rInspectSnapshot(symbols=("A",), required_bundle_fields=("bars",))
    snapshot = {"bundle": {"A": bar(1)}, "bars": {"history": [1]}}
    assert signal.step(snapshot) == 1
    snapshot["bars"]["history"].append(2)
    assert signal.seen["bars"] == {"history": [1]}
    assert signal.seen["bundle"]["A"]["close"] == 1


def test_new_snapshots_do_not_invent_a_missing_bars_extra_field():
    signal = rInspectSnapshot(symbols=("A",), required_bundle_fields=("bars",))
    with pytest.raises(KeyError, match="bars"):
        signal.step({"bundle": {"A": bar(1)}})
    assert signal.g_index == -1 and not signal.is_faulted


def test_extra_field_mapping_does_not_change_bundle_selection():
    signal = rInspectSnapshot(symbols=("A",), bundle_key_map={"bars": "metadata"})
    assert signal.step({"bundle": {"A": bar(1)}, "metadata": "extra"}) == 1
    assert signal.seen["bars"] == "extra"
    assert dict(signal.seen)["bars"] == "extra"


def test_mapped_extra_fields_are_independent_of_bundle_and_time():
    signal = rInspectSnapshot(
        symbols=("A",),
        bundle_key_map={
            "bundle": "quotes",
            "bars": "note",
            "open_time": "timestamp",
            "bar_time": "event_time",
        },
    )
    snapshot = {
        "quotes": {"A": bar(7)},
        "note": "保留",
        "timestamp": 10,
        "event_time": 20,
    }
    assert signal.step(snapshot) == 7
    assert signal.seen["bars"] == "保留"
    assert signal.seen["bar_time"] == 20
    assert signal.meta_info["last_bar_time"] == 10
    assert dict(signal.seen)["bars"] == "保留"


def test_explicit_mapping_missing_source_never_falls_back():
    signal = rKlineBundleRank(
        symbols=("A",),
        bundle_key_map={
            "bundle": "klines",
            "bars": "bars",
            "open_time": "date",
            "bar_time": "event_time",
        },
    )
    with pytest.raises(KeyError, match="bundle"):
        signal.step({"bundle": {"A": bar(1)}, "bars": {"A": bar(2)}, "open_time": 10})
    assert signal.g_index == -1 and not signal.is_faulted
    np.testing.assert_allclose(
        signal.step({"klines": {"A": bar(1)}, "open_time": 10, "event_time": 20}), [1]
    )
    assert signal.meta_info["last_bar_time"] is None


def test_bundle_and_open_time_do_not_have_implicit_aliases():
    snapshot = {"bars": {"A": bar(1)}, "bar_time": 10}
    signal = rKlineBundleRank(symbols=("A",))
    with pytest.raises(KeyError, match="bundle"):
        signal.step(snapshot)
    assert signal.g_index == -1 and not signal.is_faulted
    mapped = rKlineBundleRank(
        symbols=("A",), bundle_key_map={"bundle": "bars", "open_time": "bar_time"}
    )
    np.testing.assert_allclose(mapped.step(snapshot), [1])
    assert mapped.meta_info["last_bar_time"] == 10
    _, meta = KlineBundleRank(
        [snapshot],
        symbols=("A",),
        bundle_key_map={"bundle": "bars", "open_time": "bar_time"},
        return_meta_info=True,
    )
    assert meta["bar_times"] == (10,)


def test_bundle_and_open_time_are_independent_of_extra_fields():
    signal = rInspectSnapshot(symbols=("A",))
    snapshot = {
        "bundle": {"A": bar(2)},
        "bars": {"A": bar(99)},
        "open_time": 10,
        "bar_time": 20,
    }
    assert signal.step(snapshot) == 2
    assert signal.seen["bars"]["A"]["close"] == 99
    assert signal.meta_info["last_bar_time"] == 10
    assert signal.step({"bundle": {"A": bar(3)}, "bar_time": 20}) == 3
    assert signal.meta_info["last_bar_time"] is None


def test_mapped_children_receive_snapshot_time_for_missing_symbols():
    class rChildTime(rKlineSignal):
        def __init__(self, **kwargs):
            super().__init__(
                {"time": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
                n_backward=0,
                required_fields=("bar_time",),
                **kwargs,
            )

        def forward(self, row):
            return float(row["bar_time"])

        @property
        def full_name(self):
            return "child_time"

    signal = rKlineBundleMapSignal(rChildTime, symbols=("A", "B"))
    snapshot = {"open_time": 10, "bundle": {"A": bar(1, bar_time=10)}}
    np.testing.assert_allclose(signal.step(snapshot), [10, 10])


def test_snapshot_time_order_is_owned_by_caller():
    signal = rKlineBundleRank(symbols=("A",))
    signal.step({"open_time": 20, "bundle": {"A": bar(1)}})
    signal.step({"open_time": 10, "bundle": {"A": bar(2)}})
    assert signal.g_index == 1 and signal.meta_info["last_bar_time"] == 10
