from __future__ import annotations

import math
from numbers import Real
from typing import Any

from pyta2.structure.channel import rBoll as _rPytaBoll
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply

from .._internal.indicator_factor import _rKlineIndicatorFactor


class rKlineBoll(_rKlineIndicatorFactor):
    """绑定到一个 K 线字段的布林带 Signal。"""

    name = "Boll"

    def __init__(
        self,
        n: int = 20,
        F: float = 2.0,
        *,
        field: str = "close",
        **kwargs: Any,
    ) -> None:
        self.n = ensure_integer(n, "n", min_value=1)
        if isinstance(F, bool) or not isinstance(F, Real):
            raise TypeError(f"F must be a real number, got {type(F).__name__}")
        normalized_F = float(F)
        if not math.isfinite(normalized_F) or normalized_F <= 0:
            raise ValueError(f"F must be a finite number greater than 0, got {F!r}")
        self.F = int(normalized_F) if normalized_F.is_integer() else normalized_F
        self.field = field
        super().__init__(
            _rPytaBoll(self.n, self.F, buffer_size=0, return_dict=False),
            fields=(field,),
            **kwargs,
        )


def KlineBoll(
    data: Any,
    n: int = 20,
    F: float = 2.0,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """批量 replay :class:`rKlineBoll`。"""

    return forward_signal_apply(
        data,
        rKlineBoll,
        param_args=(n, F),
        param_kwargs={"field": field},
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineBoll", "rKlineBoll"]
