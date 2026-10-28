from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sigma2.core import forward_signal_apply
from sigma2.kline.trend.ma import rKlineMA

from ..map import rKlineBundleMapSignal


class rKlineBundleMA(rKlineBundleMapSignal):
    """用独立单 symbol 均线，一次计算整个截面的移动平均。"""

    def __init__(
        self,
        n: int,
        *,
        symbols: Sequence[str],
        ma_type: str = "SMA",
        field: str = "close",
        ma_kwargs: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            rKlineMA,
            n,
            symbols=symbols,
            operator_kwargs={
                "ma_type": ma_type,
                "field": field,
                "ma_kwargs": ma_kwargs,
            },
            **kwargs,
        )


def KlineBundleMA(
    data: Any,
    n: int,
    *,
    symbols: Sequence[str] | None = None,
    key_map: Mapping[str, str] | None = None,
    bundle_key_map: Mapping[str, str] | None = None,
    ma_type: str = "SMA",
    field: str = "close",
    ma_kwargs: Mapping[str, Any] | None = None,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """按时点逐步重放多 symbol 均线。"""
    return forward_signal_apply(
        data,
        rKlineBundleMA,
        param_args=(n,),
        param_kwargs={"ma_type": ma_type, "field": field, "ma_kwargs": ma_kwargs},
        symbols=symbols,
        key_map=key_map,
        bundle_key_map=bundle_key_map,
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineBundleMA", "rKlineBundleMA"]
