from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from typing import Any

import numpy as np
from pyta2.base import rIndicator
from pyta2.utils.validation import ensure_integer

from sigma2.kline.signal import rKlineSignal
from sigma2.utils.pyta2 import (
    normalize_pyta2_inputs,
    resolve_pyta2_default_inputs,
    resolve_pyta2_indicator,
)


def pyta2_signal(
    indicator: str | type,
    *,
    history_window: int,
    params: dict[str, Any] | None = None,
    field: str | None = None,
    inputs: Sequence[str] | None = None,
    full_name: str | None = None,
    buffer_size: int = 1,
) -> "rPyta2Signal":
    """将指定 pyta2 指标绑定到 K 线字段。"""
    return rPyta2Signal(
        indicator,
        history_window=history_window,
        params=params,
        field=field,
        inputs=inputs,
        full_name=full_name,
        buffer_size=buffer_size,
    )


class rPyta2Signal(rKlineSignal):
    """使用调用者指定的有限输入窗口推进 pyta2 指标。"""

    def __init__(
        self,
        indicator: str | type,
        *,
        history_window: int,
        params: dict[str, Any] | None = None,
        field: str | None = None,
        inputs: Sequence[str] | None = None,
        full_name: str | None = None,
        buffer_size: int = 1,
    ) -> None:
        if field is not None and inputs is not None:
            raise ValueError("field and inputs cannot both be provided")
        indicator_cls = resolve_pyta2_indicator(indicator)
        if not issubclass(indicator_cls, rIndicator):
            raise TypeError("indicator class must derive from pyta2 rIndicator")
        options = dict(params or {})
        if {"buffer_size", "return_dict"} & options.keys():
            raise ValueError("params must not override component output settings")
        component = indicator_cls(**options, buffer_size=0, return_dict=True)
        if field is not None:
            fields = normalize_pyta2_inputs((field,))
        elif inputs is not None:
            fields = normalize_pyta2_inputs(inputs)
        else:
            fields = resolve_pyta2_default_inputs(indicator) or ("close",)
        if not fields:
            raise ValueError("inputs must contain at least one K-line field")
        self._fields = fields
        self._history_window = ensure_integer(
            history_window, "history_window", min_value=1
        )
        self._full_name = full_name
        super().__init__(
            schema=dict(component.schema.items()),
            n_backward=component.n_backward,
            buffer_size=buffer_size,
            used_fields=fields,
        )
        self._state.update(
            indicator=component, values=deque(maxlen=self.history_window)
        )

    def forward(
        self,
        open,
        high,
        low,
        close,
        volume=None,
        *,
        open_time=None,
        is_closed=True,
        is_missing=False,
    ) -> dict[str, Any]:
        fields = {
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
        values = self._state["values"]
        values.append(
            tuple(
                float("nan") if fields[name] is None else fields[name]
                for name in self.fields
            )
        )
        array = np.asarray(values, dtype=float)
        return self._state["indicator"].rolling(
            *(array[:, i] for i in range(len(self.fields)))
        )

    @property
    def fields(self) -> tuple[str, ...]:
        return self._fields

    @property
    def history_window(self) -> int:
        return self._history_window

    @property
    def full_name(self) -> str:
        if self._full_name is not None:
            return self._full_name
        return f"{self._state['indicator'].full_name}[{','.join(self.fields)}]"


__all__ = ["pyta2_signal", "rPyta2Signal"]
