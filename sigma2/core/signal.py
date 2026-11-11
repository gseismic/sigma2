from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .operator import rOperator


class rSignal(rOperator):
    """结果属于当前观测的算子。"""

    def __init__(
        self,
        *,
        schema: Mapping[str, Any] | None = None,
        n_backward: int = 0,
        buffer_size: int = 1,
    ) -> None:
        super().__init__(
            schema=schema,
            n_backward=n_backward,
            n_forward=0,
            buffer_size=buffer_size,
        )


__all__ = ["rSignal"]
