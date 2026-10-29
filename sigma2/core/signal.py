from __future__ import annotations

from typing import Any

from .operator import rOperator


class rSignal(rOperator):
    """结果属于当前观测的算子；未来期固定为零。"""

    def __init__(self, schema: Any, *, n_backward: int, **kwargs: Any) -> None:
        super().__init__(schema, n_backward=n_backward, n_forward=0, **kwargs)


__all__ = ["rSignal"]
