from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from typing import Any

import numpy as np
from pyta2.trend.ma.api import get_ma_class
from pyta2.utils.space import Scalar
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply, rKlineWindowSignal
from sigma2.core._indicator_factor import rolling_with_nan_recovery
from sigma2.utils.pyta2 import normalize_pyta2_inputs


class rKlineMeanOfMeanV2(rKlineWindowSignal):
    """组合两个 pyta2 均线，保持单 symbol 的递推状态。"""

    name = "mean_of_mean_v2"

    def __init__(
        self,
        inner_n: int = 3,
        outer_n: int = 3,
        *,
        ma_type: str = "SMA",
        field: str = "close",
        ma_kwargs: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.inner_n = ensure_integer(inner_n, "inner_n", min_value=1)
        self.outer_n = ensure_integer(outer_n, "outer_n", min_value=1)
        self.field = normalize_pyta2_inputs((field,))[0]
        if ma_kwargs is not None and not isinstance(ma_kwargs, Mapping):
            raise TypeError("ma_kwargs must be a mapping or None")
        self.ma_kwargs = dict(ma_kwargs or {})
        forbidden = {
            "buffer_size",
            "return_dict",
            "buffer_factor",
            "n",
            "n1",
        } & self.ma_kwargs.keys()
        if forbidden:
            raise ValueError(f"ma_kwargs cannot override {sorted(forbidden)}")
        ma_cls = get_ma_class(ma_type)
        self._inner = ma_cls(
            self.inner_n, buffer_size=0, return_dict=False, **self.ma_kwargs
        )
        self._outer = ma_cls(
            self.outer_n, buffer_size=0, return_dict=False, **self.ma_kwargs
        )
        self.ma_type = str(self._inner.name)
        super().__init__(
            schema={"mean_of_mean": Scalar(low=-np.inf, high=np.inf, dtype=np.float64)},
            n_backward=self._inner.n_backward + self._outer.n_backward,
            history_window=self._inner.min_periods,
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        self._inner.reset()
        self._outer.reset()
        self._inner_values = deque(maxlen=self._outer.min_periods)

    def forward(self, opens, highs, lows, closes, volumes) -> float:
        if self._lifecycle_mode != "step":
            raise RuntimeError(
                "mean_of_mean_v2 requires step() to advance child indicators"
            )
        arrays = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }
        values = arrays[self.field]
        middle = rolling_with_nan_recovery(self._inner, values)
        self._inner_values.append(middle)
        return float(
            rolling_with_nan_recovery(
                self._outer, np.asarray(self._inner_values, dtype=float)
            )
        )

    @property
    def full_name(self) -> str:
        def component_name(component):
            name = component.full_name
            if component.name == "KAMA" and component.stride != 1:
                name = f"{name[:-1]},stride={component.stride})"
            return name

        return f"mean_of_mean_v2({component_name(self._inner)},{component_name(self._outer)})[{self.field}]"

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info.update(
            {
                "field": self.field,
                "ma_type": self.ma_type,
                "ma_kwargs": dict(self.ma_kwargs),
            }
        )
        return info


def KlineMeanOfMeanV2(
    data: Any,
    inner_n: int = 3,
    outer_n: int = 3,
    *,
    ma_type: str = "SMA",
    field: str = "close",
    ma_kwargs: Mapping[str, Any] | None = None,
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbol: str | None = None,
) -> Any:
    """逐时点重放两级均线。"""
    return forward_signal_apply(
        data,
        rKlineMeanOfMeanV2,
        param_args=(inner_n, outer_n),
        param_kwargs={"ma_type": ma_type, "field": field, "ma_kwargs": ma_kwargs},
        return_type=return_type,
        return_meta_info=return_meta_info,
        symbol=symbol,
    )


__all__ = ["KlineMeanOfMeanV2", "rKlineMeanOfMeanV2"]
