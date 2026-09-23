from __future__ import annotations

from typing import Any

from pyta2.stats.atr import rATR as _rPytaATR
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply

from .._internal.indicator_factor import _rKlineIndicatorFactor


class rKlineATR(_rKlineIndicatorFactor):
    """固定使用 high/low/close 的平均真实波幅 Signal。"""

    name = "ATR"

    def __init__(
        self,
        n: int = 20,
        *,
        ma_type: str = "EMA",
        **kwargs: Any,
    ) -> None:
        self.n = ensure_integer(n, "n", min_value=1)
        indicator = _rPytaATR(
            self.n,
            ma_type=ma_type,
            buffer_size=0,
            return_dict=False,
        )
        self.ma_type = str(indicator.fn_ma.name)
        indicator.ma_type = self.ma_type
        super().__init__(
            indicator,
            fields=("high", "low", "close"),
            # n=1 时仍需保留前收盘价，才能计算第二根及之后的 True Range。
            history_window=max(indicator.required_window, 2),
            **kwargs,
        )


def KlineATR(
    data: Any,
    n: int = 20,
    *,
    ma_type: str = "EMA",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """批量 replay :class:`rKlineATR`。"""

    return forward_signal_apply(
        data,
        rKlineATR,
        param_args=(n,),
        param_kwargs={"ma_type": ma_type},
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineATR", "rKlineATR"]
