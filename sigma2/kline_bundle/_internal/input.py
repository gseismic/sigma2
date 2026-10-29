from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from types import MappingProxyType
from typing import Any

import numpy as np
from pyta2.utils.validation import ensure_integer

from sigma2.kline._internal.data import (
    FieldView,
    input_value,
    normalize_field_names,
    normalize_key_map,
    normalize_required_fields,
    normalize_symbols,
    numeric_values,
    require_fields,
)
from sigma2.kline._internal.input import prepare_kline_bar

from .symbol_table import SymbolTable


class _BundleView(Mapping[str, Any]):
    """把截面字典转换为可读取字段的固定 symbol 视图。"""

    def __init__(
        self,
        raw: Mapping[str, Any],
        symbols: tuple[str, ...],
        key_map: Mapping[str, str],
        bundle_key_map: Mapping[str, str],
        required_fields: Sequence[str],
        required_bundle_fields: Sequence[str],
    ) -> None:
        self._data = FieldView(
            raw,
            bundle_key_map,
            snapshot_fields=tuple(
                field for field in required_bundle_fields if field != "bundle"
            ),
        )
        if "bundle" not in self._data:
            raise KeyError("snapshot is missing required field: 'bundle'")
        bars = self._data["bundle"]
        if not isinstance(bars, Mapping):
            raise TypeError("snapshot bundle must be a mapping from symbols to bars")
        self.symbols = symbols
        self._required_fields = tuple(required_fields)
        if "symbols" in self._data:
            if normalize_symbols(self._data["symbols"]) != symbols:
                raise ValueError("bundle symbols and order must match the operator")
        unknown = set(bars) - set(symbols)
        if unknown:
            raise ValueError(
                f"bars contain unknown symbols: {sorted(unknown, key=str)}"
            )
        prepared_bars = {}
        for symbol, bar in bars.items():
            if not isinstance(bar, Mapping):
                raise TypeError(f"bar for {symbol!r} must be a mapping")
            prepared_bars[symbol] = prepare_kline_bar(bar, key_map, required_fields)
        self._bars = MappingProxyType(prepared_bars)

    def __getitem__(self, key: str) -> Any:
        if key == "bundle":
            return self._bars
        if key == "symbols":
            return self.symbols
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(dict.fromkeys((*self._data, "bundle", "symbols")))

    def __len__(self) -> int:
        return len(tuple(iter(self)))

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    @property
    def present(self) -> np.ndarray:
        return np.asarray([symbol in self._bars for symbol in self.symbols], dtype=bool)

    def field(self, name: str) -> np.ndarray:
        values = [
            np.nan
            if symbol not in self._bars
            else input_value(self._bars[symbol], name, np.nan)
            for symbol in self.symbols
        ]
        return numeric_values(
            values, required=name != "volume" or "volume" in self._required_fields
        )


class _KlineBundleInput:
    """校验共同时间轴，并为每 symbol 的结果提供固定输出轴。"""

    family = "kline_bundle"
    step_input_keys = ("bundle",)

    def __init__(
        self,
        schema: Any,
        *,
        symbols: Sequence[str],
        scope: str = "all",
        per_symbol: bool = True,
        key_map: Mapping[str, str] | None = None,
        bundle_key_map: Mapping[str, str] | None = None,
        required_fields: Sequence[str] = (),
        required_bundle_fields: Sequence[str] = (),
        **kwargs: Any,
    ) -> None:
        self.symbols = normalize_symbols(symbols)
        if not isinstance(per_symbol, bool):
            raise TypeError("per_symbol must be bool")
        self.per_symbol = per_symbol
        self._key_map = normalize_key_map(key_map, "key_map")
        self._bundle_key_map = normalize_key_map(bundle_key_map, "bundle_key_map")
        self._required_fields = normalize_required_fields(required_fields)
        extra_bundle_fields = normalize_field_names(
            required_bundle_fields, "required_bundle_fields"
        )
        self._required_bundle_fields = tuple(
            dict.fromkeys(("bundle", *extra_bundle_fields))
        )
        self._last_bar_time: Any = None
        self._last_input_metadata: dict[str, Any] = {}
        super().__init__(schema, scope=scope, **kwargs)

    def _new_output_table(self, maxlen: int | None) -> Any:
        if self.per_symbol:
            return SymbolTable(self.schema, self.symbols, maxlen, self.buffer_factor)
        return super()._new_output_table(maxlen)

    def step(self, bundle: Mapping[str, Any]) -> Any:
        self._ensure_healthy()
        if not isinstance(bundle, Mapping):
            raise TypeError("step requires a bundle mapping")
        prepared = _BundleView(
            bundle,
            self.symbols,
            self._key_map,
            self._bundle_key_map,
            self.required_fields,
            self.required_bundle_fields,
        )

        require_fields(prepared, self.required_bundle_fields)
        for symbol, bar in prepared["bundle"].items():
            try:
                require_fields(bar, self.required_fields)
            except KeyError as exc:
                raise KeyError(f"bar for {symbol!r}: {exc.args[0]}") from exc
            incoming_symbol = input_value(bar, "symbol")
            if incoming_symbol is not None and incoming_symbol != symbol:
                raise ValueError(f"bar symbol does not match bundle key {symbol!r}")
        output = super().step(prepared)
        self._last_bar_time = input_value(prepared, "open_time")
        self._last_input_metadata = {
            "bar_time": self._last_bar_time,
            "available_at": input_value(prepared, "available_at"),
        }
        return output

    def reset(self) -> None:
        super().reset()
        self._last_bar_time = None
        self._last_input_metadata = {}

    @property
    def key_map(self) -> dict[str, str]:
        return dict(self._key_map)

    @property
    def bundle_key_map(self) -> dict[str, str]:
        return dict(self._bundle_key_map)

    @property
    def required_fields(self) -> tuple[str, ...]:
        return self._required_fields

    @property
    def required_bundle_fields(self) -> tuple[str, ...]:
        return self._required_bundle_fields

    def missing_symbols(self) -> Any:
        """构造各 symbol 的缺失输出，沿用每个 Space 的哨兵。"""
        values = []
        for key in self.output_keys:
            space = self.schema[key]
            shape = (len(self.symbols), *tuple(getattr(space, "shape", ())))
            dtype = object if space.null_value is None else space.dtype
            values.append(np.full(shape, space.null_value, dtype=dtype))
        return values[0] if len(values) == 1 else tuple(values)

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info.update(
            {
                "symbols": self.symbols,
                "per_symbol": self.per_symbol,
                "last_bar_time": self._last_bar_time,
                "key_map": self.key_map,
                "bundle_key_map": self.bundle_key_map,
                "required_fields": self.required_fields,
                "required_bundle_fields": self.required_bundle_fields,
            }
        )
        return info


__all__ = ["_BundleView", "_KlineBundleInput"]
