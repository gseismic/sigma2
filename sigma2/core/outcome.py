from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyta2.utils.validation import ensure_integer

from .operator import rOperator


class rOutcome(rOperator):
    """等待固定后续观测后，输出属于历史锚点的结果。"""

    def __init__(
        self,
        *,
        n_forward: int,
        schema: Mapping[str, Any] | None = None,
        n_backward: int = 0,
        buffer_size: int = 1,
    ) -> None:
        n_forward = ensure_integer(n_forward, "n_forward", min_value=1)
        super().__init__(
            schema=schema,
            n_backward=n_backward,
            n_forward=n_forward,
            buffer_size=buffer_size,
        )


__all__ = ["rOutcome"]
