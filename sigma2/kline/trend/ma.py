from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np
from pyta2.trend.ma.api import get_ma_class

from sigma2.kline.signal import rKlineSignal

_MA_TYPES = frozenset({"SMA", "EMA", "WMA", "HMA", "DEMA", "TEMA", "ZLEMA"})
_FIELDS = frozenset({"open", "high", "low", "close", "volume"})


class rKlineMA(rKlineSignal):
    """按指定 K 线字段计算单参数均线，并支持末根 K 线重算。"""

    name = "MA"

    def __init__(
        self,
        n: int,
        *,
        ma_type: str = "SMA",
        field: str = "close",
        symbol: str | None = None,
        buffer_size: int | None = 1,
    ) -> None:
        if not isinstance(ma_type, str):
            raise TypeError("ma_type must be a string")
        ma_type = ma_type.strip().upper()
        if ma_type not in _MA_TYPES:
            raise ValueError(f"unsupported single-parameter MA: {ma_type}")
        if not isinstance(field, str) or field not in _FIELDS:
            raise ValueError(f"unsupported K-line field: {field!r}")

        indicator = get_ma_class(ma_type)(n, buffer_size=0, return_dict=False)
        self._field = field
        super().__init__(
            schema={"ma": indicator.schema[indicator.output_keys[0]]},
            n_backward=indicator.n_backward,
            symbol=symbol,
            buffer_size=buffer_size,
            state={
                # 子指标及其输入窗口一起保存，盘中更新时恢复到同一时点。
                "indicator": indicator,
                "values": deque(maxlen=indicator.min_periods),
            },
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
        result = self._state["indicator"].rolling(np.asarray(values, dtype=float))
        return {"ma": result}

    def reset_extras(self) -> None:
        self._state["indicator"].reset()
        self._state["values"].clear()

    @property
    def field(self) -> str:
        return self._field

    @property
    def n(self) -> int:
        return self._state["indicator"].n

    @property
    def ma_type(self) -> str:
        return self._state["indicator"].name

    @property
    def used_fields(self) -> tuple[str, ...]:
        return (self.field,)

    @property
    def full_name(self) -> str:
        return f"{self._state['indicator'].full_name}[{self.field}]"


def KlineMA(
    data: Any,
    n: int,
    *,
    ma_type: str = "SMA",
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbol: str | None = None,
) -> Any:
    """逐条 MA 已迁移；通用批量接口等待单独迁移。"""
    raise NotImplementedError(
        "KlineMA batch requires the separate batch migration; use rKlineMA.step"
    )


__all__ = ["KlineMA", "rKlineMA"]
