from __future__ import annotations

from typing import Any

from pyta2.momentum import rKDJ as _rPytaKDJ
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply

from ._factor import _rKlineIndicatorFactor


class rKDJ(_rKlineIndicatorFactor):
    """固定使用 high/low/close 的 KDJ 因子。"""

    name = "KDJ"

    def __init__(
        self,
        n1: int = 9,
        n2: int = 3,
        n3: int = 3,
        **kwargs: Any,
    ) -> None:
        self.n1 = ensure_integer(n1, "n1", min_value=1)
        self.n2 = ensure_integer(n2, "n2", min_value=1)
        self.n3 = ensure_integer(n3, "n3", min_value=1)
        if self.n1 <= self.n2 or self.n1 <= self.n3:
            raise ValueError(
                "n1 must be greater than n2 and n3, "
                f"got n1={self.n1}, n2={self.n2}, n3={self.n3}"
            )
        super().__init__(
            _rPytaKDJ(
                self.n1,
                self.n2,
                self.n3,
                buffer_size=0,
                return_dict=False,
            ),
            fields=("high", "low", "close"),
            **kwargs,
        )


def KDJ(
    data: Any,
    n1: int = 9,
    n2: int = 3,
    n3: int = 3,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """批量 replay :class:`rKDJ`。"""

    return forward_signal_apply(
        data,
        rKDJ,
        param_args=(n1, n2, n3),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KDJ", "rKDJ"]
