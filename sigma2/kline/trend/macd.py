from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
from pyta2.trend.macd import rMACD

from sigma2.core.utils import forward_step_apply
from sigma2.kline.signal import rKlineSignal

_FIELDS = frozenset({"open", "high", "low", "close", "volume"})


class rKlineMACD(rKlineSignal):
    """按指定 K 线字段计算 MACD，并支持末根 K 线重算。"""

    name = "MACD"

    def __init__(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        *,
        field: str = "close",
        buffer_size: int = 1,
    ) -> None:
        if not isinstance(field, str) or field not in _FIELDS:
            raise ValueError(f"unsupported K-line field: {field!r}")

        indicator = rMACD(
            n1=slow,
            n2=fast,
            n3=signal,
            buffer_size=0,
            return_dict=True,
        )
        self._field = field
        super().__init__(
            schema=dict(indicator.schema.items()),
            n_backward=indicator.n_backward,
            buffer_size=buffer_size,
            used_fields=(field,),
        )
        # 指标和输入窗口一起保存，盘中更新时恢复到同一时点。
        self._state.update(
            indicator=indicator,
            values=deque(maxlen=indicator.min_periods),
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
        value = fields[self.field]
        values = self._state["values"]
        values.append(float("nan") if value is None else value)
        return self._state["indicator"].rolling(np.asarray(values, dtype=float))

    @property
    def field(self) -> str:
        return self._field

    @property
    def fast(self) -> int:
        return self._state["indicator"].n2

    @property
    def slow(self) -> int:
        return self._state["indicator"].n1

    @property
    def signal(self) -> int:
        return self._state["indicator"].n3

    @property
    def full_name(self) -> str:
        return f"{self._state['indicator'].full_name}[{self.field}]"


def KlineMACD(
    data: Iterable[Mapping[str, Any]],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """逐条重放 K 线并输出 MACD 结果。"""
    indicator = rKlineMACD(fast, slow, signal, field=field, buffer_size=0)
    return forward_step_apply(
        data, indicator, return_type=return_type, return_meta_info=return_meta_info
    )


__all__ = ["KlineMACD", "rKlineMACD"]
