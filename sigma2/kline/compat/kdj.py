from __future__ import annotations

from typing import Any

from ..momentum.kdj import KlineKDJ, rKlineKDJ
from ._warnings import warn_deprecated


class rKDJ(rKlineKDJ):
    """兼容旧名称；新代码使用 :class:`rKlineKDJ`。"""

    def __init__(
        self,
        n1: int = 9,
        n2: int = 3,
        n3: int = 3,
        **kwargs: Any,
    ) -> None:
        warn_deprecated("rKDJ", "rKlineKDJ")
        super().__init__(n1, n2, n3, **kwargs)


def KDJ(
    data: Any,
    n1: int = 9,
    n2: int = 3,
    n3: int = 3,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    warn_deprecated("KDJ", "KlineKDJ")
    return KlineKDJ(
        data,
        n1,
        n2,
        n3,
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KDJ", "rKDJ"]
