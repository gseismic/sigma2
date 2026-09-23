from __future__ import annotations

from typing import Any

from pyta2.momentum import rMACD as _rPytaMACD
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply

from .._internal.indicator_factor import _rKlineIndicatorFactor


class rKlineMACD(_rKlineIndicatorFactor):
    """绑定到一个 K 线字段的 MACD Signal。"""

    name = "MACD"

    def __init__(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        *,
        field: str = "close",
        **kwargs: Any,
    ) -> None:
        self.fast = ensure_integer(fast, "fast", min_value=1)
        self.slow = ensure_integer(slow, "slow", min_value=1)
        self.signal = ensure_integer(signal, "signal", min_value=1)
        if self.slow <= self.fast:
            raise ValueError(
                f"slow must be greater than fast, got slow={self.slow}, fast={self.fast}"
            )
        self.field = field
        super().__init__(
            _rPytaMACD(
                self.slow,
                self.fast,
                self.signal,
                buffer_size=0,
                return_dict=False,
            ),
            fields=(field,),
            **kwargs,
        )


def KlineMACD(
    data: Any,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """批量 replay :class:`rKlineMACD`。"""

    return forward_signal_apply(
        data,
        rKlineMACD,
        param_args=(fast, slow, signal),
        param_kwargs={"field": field},
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineMACD", "rKlineMACD"]
