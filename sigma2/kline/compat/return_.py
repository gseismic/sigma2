from __future__ import annotations

from typing import Any

from ..price.return_ import rKlineReturn
from ._warnings import warn_deprecated


class rReturn(rKlineReturn):
    """兼容旧名称；新代码使用 :class:`rKlineReturn`。"""

    def __init__(self, n: int = 1, **kwargs: Any) -> None:
        warn_deprecated("rReturn", "rKlineReturn")
        super().__init__(n, **kwargs)


__all__ = ["rReturn"]
