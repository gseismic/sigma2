from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pyta2.base import rIndicator

from sigma2.utils.pyta2 import (
    normalize_pyta2_inputs,
    resolve_pyta2_default_inputs,
    resolve_pyta2_indicator,
)

from ._internal.indicator_factor import _rKlineIndicatorFactor


def pyta2_signal(
    indicator: str | type,
    *,
    history_window: int,
    params: dict[str, Any] | None = None,
    field: str | None = None,
    inputs: Sequence[str] | None = None,
    **kwargs: Any,
) -> "rPyta2Signal":
    """按名称或类构造 pyta2 桥接；历史长度由调用者明确。"""
    return rPyta2Signal(
        indicator,
        history_window=history_window,
        params=params,
        field=field,
        inputs=inputs,
        **kwargs,
    )


class rPyta2Signal(_rKlineIndicatorFactor):
    """将支持有限历史窗口的 pyta2 指标应用于每个 symbol。"""

    def __init__(
        self,
        indicator: str | type,
        *,
        history_window: int,
        params: dict[str, Any] | None = None,
        field: str | None = None,
        inputs: Sequence[str] | None = None,
        full_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        if field is not None and inputs is not None:
            raise ValueError("field and inputs cannot both be provided")
        indicator_cls = resolve_pyta2_indicator(indicator)
        if not issubclass(indicator_cls, rIndicator):
            raise TypeError("indicator class must derive from pyta2 rIndicator")
        options = dict(params or {})
        if {"buffer_size", "return_dict"} & options.keys():
            raise ValueError("params must not override component output settings")
        component = indicator_cls(**options, buffer_size=0, return_dict=False)
        if field is not None:
            fields = normalize_pyta2_inputs((field,))
        elif inputs is not None:
            fields = normalize_pyta2_inputs(inputs)
        else:
            fields = resolve_pyta2_default_inputs(indicator) or ("close",)
        self._full_name = full_name
        self.indicator_params = options
        super().__init__(
            component, fields=fields, history_window=history_window, **kwargs
        )

    @property
    def full_name(self) -> str:
        if self._full_name is not None:
            return self._full_name
        return super().full_name


__all__ = ["pyta2_signal", "rPyta2Signal"]
