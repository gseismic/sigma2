from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sigma2.core import forward_outcome_apply
from sigma2.kline.outcome import rKlineFutureReturn

from ..map import rKlineBundleMapOutcome


class rKlineBundleFutureReturn(rKlineBundleMapOutcome):
    """按共同快照计算所有 symbol 的固定未来收益。"""

    def __init__(
        self,
        n_forward: int,
        *,
        symbols: Sequence[str],
        field: str = "close",
        return_type: str = "simple",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            rKlineFutureReturn,
            n_forward,
            symbols=symbols,
            operator_kwargs={"field": field, "return_type": return_type},
            **kwargs,
        )


def KlineBundleFutureReturn(
    data: Any,
    n_forward: int,
    *,
    symbols: Sequence[str] | None = None,
    field: str = "close",
    return_mode: str = "simple",
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """批量计算未来收益，结果回填到共同锚点。"""
    return forward_outcome_apply(
        data,
        rKlineBundleFutureReturn,
        param_args=(n_forward,),
        param_kwargs={"field": field, "return_type": return_mode},
        symbols=symbols,
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineBundleFutureReturn", "rKlineBundleFutureReturn"]
