from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sigma2.kline.data import KlineBar

from .data import (
    FieldView,
    input_value,
    normalize_key_map,
    normalize_required_fields,
    require_fields,
)


def prepare_kline_bar(
    bar: Any, key_map: Mapping[str, str], required_fields: Sequence[str] = ()
) -> Any:
    """把字典适配为逻辑字段快照；旧对象在无需映射时原样使用。"""
    if isinstance(bar, KlineBar):
        if not key_map:
            return bar
        fields = (
            "symbol",
            "bar_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "available_at",
            "is_missing",
        )
        return FieldView(
            {field: getattr(bar, field) for field in fields},
            key_map,
            snapshot_fields=required_fields,
        )
    if isinstance(bar, FieldView) and not key_map:
        return bar
    if isinstance(bar, Mapping):
        return FieldView(bar, key_map, snapshot_fields=required_fields)
    raise TypeError("step requires a K-line mapping or KlineBar")


class _KlineInput:
    """接收单时点行情字典，并保留旧 KlineBar 输入兼容。"""

    family = "kline"
    step_input_keys = ("bar",)

    def __init__(
        self,
        schema: Any,
        *,
        symbol: str | None = None,
        key_map: Mapping[str, str] | None = None,
        required_fields: Sequence[str] = (),
        **kwargs: Any,
    ) -> None:
        if symbol is not None and (not isinstance(symbol, str) or not symbol):
            raise ValueError("symbol must be a non-empty string or None")
        self.symbol = symbol
        self._bound_symbol = symbol
        self._key_map = normalize_key_map(key_map, "key_map")
        self._required_fields = normalize_required_fields(required_fields)
        self._last_bar_time: Any = None
        self._last_legacy_bar_time: Any = None
        self._last_input_metadata: dict[str, Any] = {}
        kwargs.setdefault("scope", symbol)
        super().__init__(schema, **kwargs)

    def step(self, bar: Mapping[str, Any] | KlineBar) -> Any:
        self._ensure_healthy()
        legacy = isinstance(bar, KlineBar)
        if legacy:
            if self._bound_symbol is not None and bar.symbol != self._bound_symbol:
                raise ValueError("bar symbol must match the operator's input stream")
            if (
                self._last_legacy_bar_time is not None
                and bar.bar_time <= self._last_legacy_bar_time
            ):
                raise ValueError("bar_time must be strictly increasing")
        prepared = prepare_kline_bar(bar, self._key_map, self.required_fields)
        require_fields(prepared, self.required_fields)
        incoming_symbol = input_value(prepared, "symbol")
        if self.symbol is not None and incoming_symbol is not None:
            if incoming_symbol != self.symbol:
                raise ValueError("bar symbol must match the operator's input stream")
        output = super().step(prepared)
        if legacy:
            self._bound_symbol = bar.symbol
            self._last_legacy_bar_time = bar.bar_time
        self._last_bar_time = input_value(prepared, "bar_time")
        self._last_input_metadata = {
            "bar_time": self._last_bar_time,
            "available_at": input_value(prepared, "available_at"),
        }
        return output

    def reset(self) -> None:
        super().reset()
        self._bound_symbol = self.symbol
        self._last_bar_time = None
        self._last_legacy_bar_time = None
        self._last_input_metadata = {}

    @property
    def key_map(self) -> dict[str, str]:
        """返回字段映射的副本，避免运行中改变输入规则。"""
        return dict(self._key_map)

    @property
    def required_fields(self) -> tuple[str, ...]:
        return self._required_fields

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info.update(
            {
                "symbol": self._bound_symbol,
                "last_bar_time": self._last_bar_time,
                "key_map": self.key_map,
                "required_fields": self.required_fields,
            }
        )
        return info


__all__ = ["_KlineInput", "prepare_kline_bar"]
