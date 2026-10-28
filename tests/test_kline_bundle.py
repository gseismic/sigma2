from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest
from pyta2.utils.space import Box, Scalar

from examples._data import make_bundles
from sigma2 import forward_outcome_apply, forward_signal_apply
from sigma2.kline import KlineBar, rKlineFutureHighLowChange, rKlineMA
from sigma2.kline_bundle import (
    KlineBundleFutureReturn,
    KlineBundleMA,
    KlineBundleRank,
    rKlineBundleFutureReturn,
    rKlineBundleMA,
    rKlineBundleMapOutcome,
    rKlineBundleMapSignal,
    rKlineBundleRank,
    rKlineBundleReturnRank,
    rKlineBundleSignal,
)


def test_data_packages_are_siblings_and_calculations_are_public():
    import sigma2
    import sigma2.kline as single
    import sigma2.kline_bundle as bundle

    assert KlineBar.__module__ == "sigma2.kline.data"
    assert sigma2.KlineBar is single.KlineBar is KlineBar
    assert sigma2.rKlineBundleRank is bundle.rKlineBundleRank
    for package in (single, bundle):
        for name in package.__all__:
            assert getattr(package, name) is not None


def test_bundle_distinguishes_missing_bar_from_invalid_field_and_copies_mapping():
    class rInspect(rKlineBundleSignal):
        def __init__(self, **kwargs):
            super().__init__(
                {"value": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
                n_backward=0,
                **kwargs,
            )

        def forward(self, snapshot):
            self.snapshot = snapshot
            self.present = snapshot.present
            return snapshot.field("close")

        @property
        def full_name(self):
            return "inspect"

    values = {"A": {"open": 1, "high": 2, "low": 0, "close": np.nan}}
    signal = rInspect(symbols=("A", "B"))
    np.testing.assert_allclose(signal.step({"bundle": values}), [np.nan, np.nan])
    values.clear()
    assert signal.snapshot["bundle"].get("A") is not None
    assert signal.snapshot["bundle"].get("B") is None
    assert signal.present.tolist() == [True, False]
    with pytest.raises(TypeError):
        signal.snapshot["bundle"]["B"] = signal.snapshot["bundle"]["A"]


def test_bundle_rejects_bad_members_before_advancing():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="unique"):
        rKlineBundleRank(symbols=("A", "A"))
    signal = rKlineBundleRank(symbols=("A",))
    with pytest.raises(ValueError, match="unknown"):
        signal.step({"bundle": {"B": {"open": 1, "high": 1, "low": 1, "close": 1}}})
    with pytest.raises(TypeError, match="mapping"):
        signal.step({"bundle": {"A": KlineBar("A", t, 1, 2, 0, 1, 5)}})
    with pytest.raises(ValueError, match="timezone"):
        KlineBar("A", t.replace(tzinfo=None), 1, 2, 0, 1, 5)
    assert signal.g_index == -1 and not signal.is_faulted


def test_cross_section_rank_ties_descending_and_missing():
    symbols = ("A", "B", "C", "D")
    bundle = make_bundles([{"A": 10, "B": 10, "C": 20}], symbols)[0]
    asc = rKlineBundleRank(symbols=symbols)
    desc = rKlineBundleRank(symbols=symbols, ascending=False)
    np.testing.assert_allclose(asc.step(bundle), [1.5, 1.5, 3, np.nan], equal_nan=True)
    np.testing.assert_allclose(desc.step(bundle), [2.5, 2.5, 1, np.nan], equal_nan=True)
    assert asc.result_index == 0


def test_return_rank_uses_common_endpoints_without_forward_fill():
    bundles = make_bundles(
        [
            {"A": 10, "B": 20},
            {"A": 11},
            {"A": 12, "B": 30},
        ]
    )
    signal = rKlineBundleReturnRank(2, symbols=("A", "B"))
    first, second, third = [signal.step(item) for item in bundles]
    assert np.isnan(first).all() and np.isnan(second).all()
    np.testing.assert_allclose(third, [1, 2])
    assert signal.n_backward == 2 and signal.min_periods == 3


def test_bundle_rejects_wrong_symbol_axis_without_advancing():
    bundles = make_bundles([{"A": 10, "B": 20}, {"A": 11, "B": 22}])
    signal = rKlineBundleRank(symbols=("A", "B"))
    signal.step(bundles[0])
    wrong_order = {**bundles[1], "symbols": ("B", "A")}
    with pytest.raises(ValueError, match="symbols"):
        signal.step(wrong_order)
    assert signal.g_index == 0 and not signal.is_faulted
    signal.step(bundles[1])
    assert signal.g_index == 1


def test_map_ma_advances_missing_symbol_and_recovers_after_window():
    bundles = make_bundles(
        [
            {"A": 10, "B": 20},
            {"A": 12},
            {"A": 14, "B": 30},
            {"A": 16, "B": 40},
        ]
    )
    signal = rKlineBundleMA(2, symbols=("A", "B"), buffer_size=-1)
    actual = np.asarray([signal.step(bundle) for bundle in bundles])
    expected = [[np.nan, np.nan], [11, np.nan], [13, np.nan], [15, 35]]
    np.testing.assert_allclose(actual, expected, equal_nan=True)
    np.testing.assert_allclose(signal.outputs["ma"], expected, equal_nan=True)
    np.testing.assert_allclose(
        KlineBundleMA(bundles, 2, return_type="tuple"), expected, equal_nan=True
    )
    assert all(child.g_index == 3 for child in signal._operators)
    signal.reset()
    replay = [signal.step(bundle) for bundle in bundles]
    np.testing.assert_allclose(replay, expected, equal_nan=True)


def test_map_adapter_rejects_wrong_base_and_reserved_options():
    with pytest.raises(TypeError, match="operator_cls"):
        rKlineBundleMapSignal(rKlineFutureHighLowChange, 1, symbols=("A",))
    with pytest.raises(ValueError, match="operator_kwargs"):
        rKlineBundleMapSignal(
            rKlineMA, 2, symbols=("A",), operator_kwargs={"buffer_size": 1}
        )
    with pytest.raises(ValueError, match="per_symbol"):
        rKlineBundleMapSignal(rKlineMA, 2, symbols=("A",), per_symbol=False)


def test_outcome_replay_aligns_anchor_and_retains_common_missing_positions():
    bundles = make_bundles(
        [
            {"A": 10, "B": 20},
            {"A": 12},
            {"A": 15, "B": 30},
            {"A": 18, "B": 40},
        ]
    )
    signal = rKlineBundleFutureReturn(
        2, symbols=("A", "B"), return_dict=True, buffer_size=-1
    )
    rows = [signal.step(bundle)["return"] for bundle in bundles]
    np.testing.assert_allclose(
        rows,
        [[np.nan, np.nan], [np.nan, np.nan], [0.5, np.nan], [0.5, np.nan]],
        equal_nan=True,
    )
    assert signal.result_index == 1
    result, meta = KlineBundleFutureReturn(bundles, 2, return_meta_info=True)
    np.testing.assert_allclose(
        next(iter(result.values())),
        [[0.5, np.nan], [0.5, np.nan], [np.nan, np.nan], [np.nan, np.nan]],
        equal_nan=True,
    )
    assert meta["symbols"] == ("A", "B")
    assert meta["emission_bar_times"] == (
        bundles[2]["open_time"],
        bundles[3]["open_time"],
        None,
        None,
    )
    assert meta["result_input_ready_at"] == (
        bundles[2]["available_at"],
        bundles[3]["available_at"],
        None,
        None,
    )


def test_outcome_mapping_supports_multiple_schema_fields():
    bundles = make_bundles([{"A": 10, "B": 20}, {"A": 12, "B": 18}])
    signal = rKlineBundleMapOutcome(rKlineFutureHighLowChange, 1, symbols=("A", "B"))
    signal.step(bundles[0])
    high, low = signal.step(bundles[1])
    np.testing.assert_allclose(high, [2.5, -1.5])
    np.testing.assert_allclose(low, [1.5, -2.5])
    assert signal.outputs["high_change"].shape == (1, 2)


def test_empty_input_and_empty_universe_have_stable_shapes():
    result, meta = KlineBundleRank([], symbols=("A", "B"), return_meta_info=True)
    assert next(iter(result.values())).shape == (0, 2)
    assert meta["symbols"] == ("A", "B")
    empty = make_bundles([{}], symbols=())[0]
    signal = rKlineBundleRank(symbols=(), buffer_size=-1)
    assert signal.step(empty).shape == (0,)
    assert signal.outputs["rank"].shape == (1, 0)
    assert KlineBundleRank([empty], return_type="tuple").shape == (1, 0)


def test_output_buffer_resize_and_latest_keep_symbol_order():
    bundles = make_bundles([{"A": 10, "B": 20}, {"A": 30, "B": 20}, {"A": 40, "B": 50}])
    signal = rKlineBundleRank(symbols=("A", "B"), buffer_size=2)
    for bundle in bundles:
        signal.step(bundle)
    np.testing.assert_allclose(signal.outputs["rank"], [[2, 1], [1, 2]])
    np.testing.assert_allclose(signal.latest["rank"], [1, 2])
    signal.resize_buffer(1)
    np.testing.assert_allclose(signal.outputs["rank"], [[1, 2]])
    signal.resize_buffer(0)
    assert signal.outputs is None and signal.latest is None
    signal.resize_buffer(-1)
    assert len(signal.outputs) == 0


class rVectorBundle(rKlineBundleSignal):
    def __init__(self, *, symbols, **kwargs):
        super().__init__(
            {"pair": Box(low=-np.inf, high=np.inf, shape=(2,), dtype=np.float64)},
            symbols=symbols,
            n_backward=0,
            **kwargs,
        )

    def forward(self, bundle):
        close = bundle.field("close")
        return np.stack([close, close * 2], axis=1)

    @property
    def full_name(self):
        return "vector"


def test_bundle_vector_space_caches_and_batches_symbol_and_value_axes():
    bundles = make_bundles([{"A": 10}, {"A": 12, "B": 20}])
    signal = rVectorBundle(symbols=("A", "B"), buffer_size=-1)
    for bundle in bundles:
        signal.step(bundle)
    expected = np.asarray([[[10, 20], [np.nan, np.nan]], [[12, 24], [20, 40]]])
    np.testing.assert_allclose(signal.outputs["pair"], expected, equal_nan=True)
    batch = forward_signal_apply(bundles, rVectorBundle, return_type="tuple")
    np.testing.assert_allclose(batch, expected, equal_nan=True)
    empty = forward_signal_apply(
        [], rVectorBundle, symbols=("A", "B"), return_type="tuple"
    )
    assert empty.shape == (0, 2, 2)


def test_bundle_scalar_output_has_no_symbol_axis():
    class rTotal(rKlineBundleSignal):
        def __init__(self, *, symbols, **kwargs):
            super().__init__(
                {"total": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
                symbols=symbols,
                n_backward=0,
                per_symbol=False,
                **kwargs,
            )

        def forward(self, bundle):
            return np.nansum(bundle.field("close"))

        @property
        def full_name(self):
            return "total"

    bundles = make_bundles([{"A": 10, "B": 20}, {"A": 12}])
    signal = rTotal(symbols=("A", "B"), buffer_size=-1)
    assert [signal.step(item) for item in bundles] == [30, 12]
    np.testing.assert_allclose(signal.outputs["total"], [30, 12])
    np.testing.assert_allclose(
        forward_signal_apply(bundles, rTotal, return_type="tuple"), [30, 12]
    )


def test_dataframe_has_time_symbol_index_and_order():
    pd = pytest.importorskip("pandas")
    bundles = make_bundles([{"A": 10, "B": 20}, {"A": 12}])
    frame = KlineBundleRank(bundles, return_type="dataframe")
    assert isinstance(frame.index, pd.MultiIndex)
    assert frame.index.names == ["bar_time", "symbol"]
    assert list(frame.index.get_level_values("symbol")) == ["A", "B", "A", "B"]
    np.testing.assert_allclose(frame.iloc[:, 0], [1, 2, 1, np.nan], equal_nan=True)


def test_missing_input_availability_is_not_guessed():
    base = make_bundles([{"A": 10}, {"A": 12}], symbols=("A",))
    unknown = {key: value for key, value in base[0].items() if key != "available_at"}
    _, meta = forward_outcome_apply(
        [unknown, base[1]],
        rKlineBundleFutureReturn,
        param_args=(1,),
        return_meta_info=True,
    )
    assert meta["result_input_ready_at"] == (None, None)


def test_missing_kama_window_recovers_instead_of_retaining_nan():
    values = [10.0, 11.0, 12.0, 13.0, 14.0, np.nan, 15.0, 16.0, 17.0, 18.0, 19.0]
    bundles = make_bundles(
        [{"A": x} if np.isfinite(x) else {} for x in values], symbols=("A",)
    )
    signal = rKlineBundleMA(
        3, symbols=("A",), ma_type="KAMA", ma_kwargs={"n2": 2, "n3": 4}
    )
    outputs = [signal.step(bundle)[0] for bundle in bundles]
    assert np.isnan(outputs[5])
    assert np.isfinite(outputs[-1])
    signal.reset()
    np.testing.assert_allclose(
        outputs, [signal.step(bundle)[0] for bundle in bundles], equal_nan=True
    )


def test_map_failure_locks_parent_until_reset_and_full_replay():
    from sigma2.kline import rKlineSignal

    class rAccumulator(rKlineSignal):
        def __init__(self, **kwargs):
            super().__init__(
                {"sum": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
                n_backward=0,
                **kwargs,
            )

        def reset_extras(self):
            self.total = 0.0

        def forward(self, bar):
            self.total += bar.close
            if bar.close < 0:
                raise ValueError("negative")
            return self.total

        @property
        def full_name(self):
            return "accumulator"

    good, bad, after = make_bundles(
        [{"A": 1, "B": 10}, {"A": 2, "B": -1}, {"A": 3, "B": 30}]
    )
    signal = rKlineBundleMapSignal(rAccumulator, symbols=("A", "B"))
    np.testing.assert_allclose(signal.step(good), [1, 10])
    with pytest.raises(ValueError, match="negative"):
        signal.step(bad)
    assert signal.is_faulted and signal.g_index == 0
    with pytest.raises(RuntimeError, match="reset"):
        signal.step(after)
    signal.reset()
    np.testing.assert_allclose(signal.step(good), [1, 10])
    np.testing.assert_allclose(signal.step(after), [4, 40])


def test_schema_shape_mismatch_locks_parent_until_reset():
    class rWrongShape(rVectorBundle):
        def forward(self, bundle):
            return np.array([1.0])

    signal = rWrongShape(symbols=("A", "B"))
    with pytest.raises(ValueError, match="shape"):
        signal.step(make_bundles([{"A": 1}])[0])
    assert signal.is_faulted and signal.g_index == -1
    signal.reset()
    assert not signal.is_faulted


def test_polars_result_keeps_time_and_symbol_columns():
    pytest.importorskip("polars")
    bundles = make_bundles([{"A": 10, "B": 20}, {"A": 12}])
    frame = KlineBundleRank(bundles, return_type="pl.dataframe")
    assert frame.columns[:2] == ["bar_time", "symbol"]
    assert frame["symbol"].to_list() == ["A", "B", "A", "B"]
    np.testing.assert_allclose(
        frame[frame.columns[-1]].to_numpy(), [1, 2, 1, np.nan], equal_nan=True
    )
