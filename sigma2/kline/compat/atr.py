from __future__ import annotations

from typing import Any

from ..volatility.atr import KlineATR, rKlineATR
from ._warnings import warn_deprecated


class rATR(rKlineATR):
    """兼容旧名称；新代码使用 :class:`rKlineATR`。"""

    def __init__(
        self,
        n: int = 20,
        *,
        ma_type: str = "EMA",
        **kwargs: Any,
    ) -> None:
        warn_deprecated("rATR", "rKlineATR")
        super().__init__(n, ma_type=ma_type, **kwargs)


def ATR(
    data: Any,
    n: int = 20,
    *,
    ma_type: str = "EMA",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    warn_deprecated("ATR", "KlineATR")
    return KlineATR(
        data,
        n,
        ma_type=ma_type,
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["ATR", "rATR"]
