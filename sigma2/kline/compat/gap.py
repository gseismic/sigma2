from __future__ import annotations

from typing import Any

from ..price.gap import rKlineGap
from ._warnings import warn_deprecated


class rGap(rKlineGap):
    """兼容旧名称；新代码使用 :class:`rKlineGap`。"""

    def __init__(self, **kwargs: Any) -> None:
        warn_deprecated("rGap", "rKlineGap")
        super().__init__(**kwargs)


__all__ = ["rGap"]
