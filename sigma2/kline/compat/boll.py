from __future__ import annotations

from typing import Any

from ..volatility.boll import KlineBoll, rKlineBoll
from ._warnings import warn_deprecated


class rBoll(rKlineBoll):
    """兼容旧名称；新代码使用 :class:`rKlineBoll`。"""

    def __init__(
        self,
        n: int = 20,
        F: float = 2.0,
        *,
        field: str = "close",
        **kwargs: Any,
    ) -> None:
        warn_deprecated("rBoll", "rKlineBoll")
        super().__init__(n, F, field=field, **kwargs)


def Boll(
    data: Any,
    n: int = 20,
    F: float = 2.0,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    warn_deprecated("Boll", "KlineBoll")
    return KlineBoll(
        data,
        n,
        F,
        field=field,
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["Boll", "rBoll"]
