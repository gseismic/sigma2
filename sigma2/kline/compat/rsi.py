from __future__ import annotations

from typing import Any

from ..momentum.rsi import KlineRSI, rKlineRSI
from ._warnings import warn_deprecated


class rRSI(rKlineRSI):
    """兼容旧名称；新代码使用 :class:`rKlineRSI`。"""

    def __init__(
        self,
        n: int = 14,
        *,
        field: str = "close",
        **kwargs: Any,
    ) -> None:
        warn_deprecated("rRSI", "rKlineRSI")
        super().__init__(n, field=field, **kwargs)


def RSI(
    data: Any,
    n: int = 14,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    warn_deprecated("RSI", "KlineRSI")
    return KlineRSI(
        data,
        n,
        field=field,
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["RSI", "rRSI"]
