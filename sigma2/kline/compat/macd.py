from __future__ import annotations

from typing import Any

from ..trend.macd import KlineMACD, rKlineMACD
from ._warnings import warn_deprecated


class rMACD(rKlineMACD):
    """兼容旧名称；新代码使用 :class:`rKlineMACD`。"""

    def __init__(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        *,
        field: str = "close",
        **kwargs: Any,
    ) -> None:
        warn_deprecated("rMACD", "rKlineMACD")
        super().__init__(fast, slow, signal, field=field, **kwargs)


def MACD(
    data: Any,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    warn_deprecated("MACD", "KlineMACD")
    return KlineMACD(
        data,
        fast,
        slow,
        signal,
        field=field,
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["MACD", "rMACD"]
