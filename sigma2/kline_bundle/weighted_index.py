from __future__ import annotations

from collections.abc import Iterable, Mapping
from fractions import Fraction
from math import fsum, isfinite
from sys import float_info
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.core.utils import forward_step_apply

from .signal import rKlineBundleSignal

_PRICE_FIELDS = frozenset({"open", "high", "low", "close"})


def _weighted_average(
    values: Iterable[tuple[float, float]], scale: float, total: float
) -> float:
    """精确累计极小贡献，避免过早转换为浮点。"""
    precise = Fraction(0)

    def contributions() -> Iterable[float]:
        nonlocal precise
        for price, weight in values:
            share = weight / scale / total
            contribution = price * share
            if share >= float_info.min and (
                price == 0 or abs(contribution) >= float_info.min
            ):
                yield contribution
            else:
                precise += (
                    Fraction(float(price))
                    * Fraction(float(weight))
                    / Fraction(float(scale))
                    / Fraction(float(total))
                )

    ordinary = fsum(contributions())
    return float(Fraction(ordinary) + precise) if precise else ordinary


class rKlineBundleFixedWeightIndex(rKlineBundleSignal):
    """按固定权重计算当前截面的价格加权平均值。

    index = sum(price_i * weight_i) / sum(weight_i)。
    构造时提供各 symbol 的非负权重，至少一个为正，零权重不参与计算；
    price 由 field 指定，默认使用 close，输出为 {"index": value}。

    has_missing=False 时，调用方保证参与成分的价格完整且有效。
    has_missing=True 时，参与成分缺失或价格无效则返回 NaN；
    固定成分以外的缺失不影响结果。
    """

    name = "FixedWeightIndex"

    def __init__(
        self,
        weights: Mapping[str, float],
        *,
        field: str = "close",
        buffer_size: int = 1,
    ) -> None:
        if not isinstance(field, str) or field not in _PRICE_FIELDS:
            raise ValueError(f"unsupported K-line price field: {field!r}")

        copied = {symbol: float(weight) for symbol, weight in weights.items()}
        if not copied or any(not isfinite(w) or w < 0 for w in copied.values()):
            raise ValueError("weights must contain finite nonnegative values")
        scale = max(copied.values())
        if scale == 0:
            raise ValueError("at least one weight must be positive")
        self._weights = tuple(
            (symbol, weight) for symbol, weight in copied.items() if weight > 0
        )
        self._weight_scale = scale
        self._weight_total = fsum(weight / scale for _, weight in self._weights)
        self._field = field
        super().__init__(
            schema={"index": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            buffer_size=buffer_size,
            used_fields=(field,),
        )

    def forward(
        self,
        bundle: Mapping[str, Mapping[str, Any]],
        *,
        open_time: Any = None,
        has_missing: bool = False,
    ) -> dict[str, float]:
        if has_missing:
            for symbol, _ in self._weights:
                bar = bundle.get(symbol)
                if bar is None or bar.get("is_missing", False):
                    return {"index": float("nan")}
                price = bar.get(self.field)
                if price is None or not isfinite(price):
                    return {"index": float("nan")}

        return {
            "index": _weighted_average(
                (
                    (bundle[symbol][self.field], weight)
                    for symbol, weight in self._weights
                ),
                self._weight_scale,
                self._weight_total,
            )
        }

    @property
    def field(self) -> str:
        return self._field

    @property
    def weights(self) -> dict[str, float]:
        """返回原始正权重成分的副本。"""
        return dict(self._weights)

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.field},weights={dict(sorted(self._weights))})"


class rKlineBundleMarketCapWeightedIndex(rKlineBundleSignal):
    """按实时市值计算当前截面的价格加权平均值。

    index = sum(price_i * market_cap_i) / sum(market_cap_i)。
    每次从 bundle 各 symbol 的 market_cap 获取非负市值，零市值不参与计算；
    price 由 field 指定，默认使用 close，输出为 {"index": value}。

    has_missing=False 时，调用方保证价格和市值完整且有效。
    has_missing=True 时无法确定缺失的市值成分，返回 NaN；
    空截面或全部市值为零时也返回 NaN。
    """

    name = "MarketCapWeightedIndex"

    def __init__(self, *, field: str = "close", buffer_size: int = 1) -> None:
        if not isinstance(field, str) or field not in _PRICE_FIELDS:
            raise ValueError(f"unsupported K-line price field: {field!r}")

        self._field = field
        super().__init__(
            schema={"index": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            buffer_size=buffer_size,
            used_fields=(field, "market_cap"),
        )

    def forward(
        self,
        bundle: Mapping[str, Mapping[str, Any]],
        *,
        open_time: Any = None,
        has_missing: bool = False,
    ) -> dict[str, float]:
        if has_missing:
            return {"index": float("nan")}

        scale = max((bar["market_cap"] for bar in bundle.values()), default=0)
        if scale == 0:
            return {"index": float("nan")}
        total = fsum(bar["market_cap"] / scale for bar in bundle.values())
        return {
            "index": _weighted_average(
                (
                    (bar[self.field], bar["market_cap"])
                    for bar in bundle.values()
                    if bar["market_cap"] != 0
                ),
                scale,
                total,
            )
        }

    @property
    def field(self) -> str:
        return self._field

    @property
    def full_name(self) -> str:
        return f"{self.name}({self.field})"


def KlineBundleFixedWeightIndex(
    data: Iterable[Mapping[str, Any]],
    weights: Mapping[str, float],
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """逐个截面重放固定权重价格指数。"""
    return forward_step_apply(
        data,
        rKlineBundleFixedWeightIndex(weights, field=field, buffer_size=0),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


def KlineBundleMarketCapWeightedIndex(
    data: Iterable[Mapping[str, Any]],
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """逐个截面重放实时市值加权价格指数。"""
    return forward_step_apply(
        data,
        rKlineBundleMarketCapWeightedIndex(field=field, buffer_size=0),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = [
    "KlineBundleFixedWeightIndex",
    "KlineBundleMarketCapWeightedIndex",
    "rKlineBundleFixedWeightIndex",
    "rKlineBundleMarketCapWeightedIndex",
]
