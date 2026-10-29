from __future__ import annotations

from typing import Any

from pyta2.utils.validation import ensure_integer

from .operator import rOperator


class rOutcome(rOperator):
    """等待固定后续观测后，输出属于历史锚点的结果。"""

    def __init__(
        self, schema: Any, *, n_backward: int, n_forward: int, **kwargs: Any
    ) -> None:
        n_forward = ensure_integer(n_forward, "n_forward", min_value=1)
        super().__init__(schema, n_backward=n_backward, n_forward=n_forward, **kwargs)


__all__ = ["rOutcome"]
