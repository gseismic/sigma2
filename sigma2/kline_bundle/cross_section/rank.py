from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.core import (
    forward_signal_apply,
    rKlineBundleSignal,
    rKlineBundleWindowSignal,
)
from sigma2.core._kline_data import include_required_fields
from sigma2.utils.pyta2 import normalize_pyta2_inputs


def _rank(values: np.ndarray, ascending: bool) -> np.ndarray:
    """有效值从 1 开始排名，完全相同的数值取平均名次。"""
    result = np.full(values.shape, np.nan)
    valid_indices = np.flatnonzero(np.isfinite(values))
    valid = values[valid_indices]
    order = np.argsort(valid if ascending else -valid, kind="stable")
    sorted_values = valid[order]
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and sorted_values[end] == sorted_values[start]:
            end += 1
        result[valid_indices[order[start:end]]] = (start + 1 + end) / 2.0
        start = end
    return result


class rKlineBundleRank(rKlineBundleSignal):
    """对当前截面中有效的 K 线字段做排名。"""

    name = "kline_rank"

    def __init__(
        self, *, field: str = "close", ascending: bool = True, **kwargs: Any
    ) -> None:
        self.field = normalize_pyta2_inputs((field,))[0]
        if not isinstance(ascending, bool):
            raise TypeError("ascending must be bool")
        self.ascending = ascending
        include_required_fields(kwargs, self.field)
        super().__init__(
            schema={"rank": Scalar(low=1, high=np.inf, dtype=np.float64)},
            n_backward=0,
            **kwargs,
        )

    def forward(self, bundle) -> np.ndarray:
        return _rank(bundle.field(self.field), self.ascending)

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.field},ascending={self.ascending})"


class rKlineBundleReturnRank(rKlineBundleWindowSignal):
    """按共同时间轴计算 N 步收益，再对有效结果排名。"""

    name = "kline_return_rank"

    def __init__(
        self, n: int = 1, *, field: str = "close", ascending: bool = True, **kwargs: Any
    ) -> None:
        self.n = ensure_integer(n, "n", min_value=1)
        self.field = normalize_pyta2_inputs((field,))[0]
        if not isinstance(ascending, bool):
            raise TypeError("ascending must be bool")
        self.ascending = ascending
        include_required_fields(kwargs, self.field)
        super().__init__(
            schema={"rank": Scalar(low=1, high=np.inf, dtype=np.float64)},
            n_backward=self.n,
            history_window=self.n + 1,
            **kwargs,
        )

    def forward(self, opens, highs, lows, closes, volumes) -> np.ndarray:
        if len(closes) <= self.n:
            return np.full(len(self.symbols), np.nan)
        values = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }[self.field]
        anchor, end = values[0], values[-1]
        valid = np.isfinite(anchor) & np.isfinite(end) & (anchor != 0)
        returns = np.full(len(self.symbols), np.nan)
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            np.divide(end, anchor, out=returns, where=valid)
            returns[valid] -= 1.0
        return _rank(returns, self.ascending)

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.n},{self.field},ascending={self.ascending})"


def KlineBundleRank(
    data: Any,
    *,
    field: str = "close",
    ascending: bool = True,
    scope: str = "all",
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbols: Sequence[str] | None = None,
    key_map: Mapping[str, str] | None = None,
    bundle_key_map: Mapping[str, str] | None = None,
) -> Any:
    """逐时点重放横截面字段排名。"""
    return forward_signal_apply(
        data,
        rKlineBundleRank,
        param_kwargs={"field": field, "ascending": ascending, "scope": scope},
        return_type=return_type,
        return_meta_info=return_meta_info,
        symbols=symbols,
        key_map=key_map,
        bundle_key_map=bundle_key_map,
    )


def KlineBundleReturnRank(
    data: Any,
    n: int = 1,
    *,
    field: str = "close",
    ascending: bool = True,
    scope: str = "all",
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbols: Sequence[str] | None = None,
    key_map: Mapping[str, str] | None = None,
    bundle_key_map: Mapping[str, str] | None = None,
) -> Any:
    """逐时点重放收益排名。"""
    return forward_signal_apply(
        data,
        rKlineBundleReturnRank,
        param_args=(n,),
        param_kwargs={"field": field, "ascending": ascending, "scope": scope},
        return_type=return_type,
        return_meta_info=return_meta_info,
        symbols=symbols,
        key_map=key_map,
        bundle_key_map=bundle_key_map,
    )


__all__ = [
    "KlineBundleRank",
    "KlineBundleReturnRank",
    "rKlineBundleRank",
    "rKlineBundleReturnRank",
]
