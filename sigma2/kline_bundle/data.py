from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from types import MappingProxyType
from typing import Any

import numpy as np
from numpy.typing import NDArray

from sigma2.core._kline_data import normalize_symbols, utc_time
from sigma2.kline.data import KlineBar


@dataclass(frozen=True, slots=True)
class KlineBundle:
    """同一时点的多 symbol K 线快照，支持横截面和共同时间推进。"""

    bar_time: datetime
    symbols: tuple[str, ...]
    interval: str
    time_label: str
    bars: Mapping[str, KlineBar]
    available_at: datetime | None = None
    _symbol_set: frozenset[str] = dataclass_field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "bar_time", utc_time(self.bar_time, "bar_time"))
        object.__setattr__(self, "symbols", normalize_symbols(self.symbols))
        object.__setattr__(self, "_symbol_set", frozenset(self.symbols))
        for name in ("interval", "time_label"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be a non-empty string")
        if self.available_at is not None:
            object.__setattr__(
                self, "available_at", utc_time(self.available_at, "available_at")
            )
        if not isinstance(self.bars, Mapping):
            raise TypeError("bars must be a mapping from symbols to KlineBar")
        bars = dict(self.bars)
        unknown = set(bars) - self._symbol_set
        if unknown:
            raise ValueError(f"bars contain unknown symbols: {sorted(unknown)}")
        for symbol, bar in bars.items():
            if not isinstance(bar, KlineBar):
                raise TypeError(f"bar for {symbol!r} must be a KlineBar")
            if bar.is_missing:
                raise ValueError("omit a missing bar from bundle.bars")
            if bar.symbol != symbol or bar.bar_time != self.bar_time:
                raise ValueError(f"bar identity or time does not match {symbol!r}")
            if (
                self.available_at is not None
                and bar.available_at is not None
                and self.available_at < bar.available_at
            ):
                raise ValueError("bundle cannot be available before a contained bar")
        object.__setattr__(self, "bars", MappingProxyType(bars))

    def get(self, symbol: str) -> KlineBar | None:
        """返回已有 Bar；已知 symbol 缺失时返回 None。"""
        if symbol not in self._symbol_set:
            raise KeyError(symbol)
        return self.bars.get(symbol)

    @property
    def present(self) -> NDArray[np.bool_]:
        """标记 Bar 是否存在，不把 NaN 字段当成缺失 Bar。"""
        return np.asarray([symbol in self.bars for symbol in self.symbols], dtype=bool)

    def field(self, name: str) -> NDArray[np.float64]:
        """按固定 symbol 顺序取字段；缺失 Bar 对应 NaN。"""
        if name not in {"open", "high", "low", "close", "volume"}:
            raise KeyError(name)
        values: list[Any] = []
        for symbol in self.symbols:
            bar = self.bars.get(symbol)
            values.append(np.nan if bar is None else getattr(bar, name))
        return np.asarray(values, dtype=np.float64)


__all__ = ["KlineBundle"]
