from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from typing import Any

import numpy as np
from pyta2.utils.space import Scalar

from sigma2.batch import forward_signal_apply
from sigma2.kline._internal.data import include_required_fields
from sigma2.kline.signal import rKlineSignal

_FIELD_INDEX = {"open": 0, "high": 1, "low": 2, "close": 3, "volume": 4}


class rKlineMeanOfMean(rKlineSignal):
    """对 K 线字段先取内层简单均值，再取外层简单均值。"""

    name = "mean_of_mean"

    def __init__(
        self,
        inner_n: int = 3,
        outer_n: int = 3,
        *,
        field: str = "close",
        **kwargs: Any,
    ) -> None:
        for label, value in (("inner_n", inner_n), ("outer_n", outer_n)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{label} must be a positive integer, got {value!r}")
        if not isinstance(field, str) or field not in _FIELD_INDEX:
            raise ValueError(
                f"field must be one of {tuple(_FIELD_INDEX)}, got {field!r}"
            )
        self.inner_n = inner_n
        self.outer_n = outer_n
        self.field = field
        include_required_fields(kwargs, self.field)
        super().__init__(
            n_backward=inner_n + outer_n - 2,
            schema={"mean_of_mean": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            **kwargs,
        )

    def reset_extras(self) -> None:
        self._inner_values = deque(maxlen=self.inner_n)
        self._outer_values = deque(maxlen=self.outer_n)

    def forward(self, bar) -> float:
        self._inner_values.append(float(getattr(bar, self.field)))
        if len(self._inner_values) < self.inner_n:
            return float("nan")
        self._outer_values.append(float(np.mean(self._inner_values)))
        if len(self._outer_values) < self.outer_n:
            return float("nan")
        return float(np.mean(self._outer_values))

    @property
    def full_name(self) -> str:
        return f"mean_of_mean({self.inner_n},{self.outer_n})[{self.field}]"


def KlineMeanOfMean(
    data: Any,
    inner_n: int = 3,
    outer_n: int = 3,
    *,
    field: str = "close",
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbol: str | None = None,
    key_map: Mapping[str, str] | None = None,
) -> Any:
    """逐根重放 :class:`rKlineMeanOfMean`。"""

    return forward_signal_apply(
        data,
        rKlineMeanOfMean,
        param_args=(inner_n, outer_n),
        param_kwargs={"field": field},
        return_type=return_type,
        return_meta_info=return_meta_info,
        symbol=symbol,
        key_map=key_map,
    )


__all__ = ["KlineMeanOfMean", "rKlineMeanOfMean"]
