from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..trend.ma import KlineMA, rKlineMA
from ._warnings import warn_deprecated


class rMA(rKlineMA):
    """兼容旧名称；新代码使用 :class:`rKlineMA`。"""

    def __init__(
        self,
        n: int,
        *,
        ma_type: str = "SMA",
        field: str = "close",
        ma_kwargs: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        warn_deprecated("rMA", "rKlineMA")
        super().__init__(
            n,
            ma_type=ma_type,
            field=field,
            ma_kwargs=ma_kwargs,
            **kwargs,
        )


def MA(
    data: Any,
    n: int,
    *,
    ma_type: str = "SMA",
    field: str = "close",
    ma_kwargs: Mapping[str, Any] | None = None,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    warn_deprecated("MA", "KlineMA")
    return KlineMA(
        data,
        n,
        ma_type=ma_type,
        field=field,
        ma_kwargs=ma_kwargs,
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["MA", "rMA"]
