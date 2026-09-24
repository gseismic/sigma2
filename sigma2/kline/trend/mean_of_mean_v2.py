from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from typing import Any

import numpy as np
from pyta2.base import rIndicator
from pyta2.trend.ma.api import get_ma_class
from pyta2.utils.validation import ensure_integer

from sigma2.core import forward_signal_apply, rKlineWindowSignal
from sigma2.utils.pyta2 import Pyta2Component


_FIELD_INDEX = {"open": 0, "high": 1, "low": 2, "close": 3, "volume": 4}
_FORBIDDEN_MA_KWARGS = {
    "buffer_size",
    "return_dict",
    "buffer_factor",
    "extra_window",
    "n",
    "n1",
}


def _component_full_name(indicator: rIndicator) -> str:
    name = indicator.full_name
    if indicator.name == "KAMA" and indicator.stride != 1:
        return f"{name[:-1]},stride={indicator.stride})"
    return name


class rKlineMeanOfMeanV2(rKlineWindowSignal):
    """用两个 pyta2 MA 组件计算 K 线字段的两级均值。"""

    name = "mean_of_mean_v2"
    checkpoint_fields = ("_inner_values",)

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
        if not isinstance(field, str) or field not in _FIELD_INDEX:
            raise ValueError(
                f"field must be one of {tuple(_FIELD_INDEX)}, got {field!r}"
            )
        if ma_kwargs is not None and not isinstance(ma_kwargs, Mapping):
            raise TypeError(
                f"ma_kwargs must be a mapping or None, got {type(ma_kwargs).__name__}"
            )
        component_kwargs = dict(ma_kwargs or {})
        forbidden = _FORBIDDEN_MA_KWARGS & component_kwargs.keys()
        if forbidden:
            raise ValueError(
                "ma_kwargs must not override lifecycle or primary window arguments: "
                f"{sorted(forbidden)}"
            )

        ma_cls = get_ma_class(ma_type)
        self._inner = ma_cls(
            self.inner_n, buffer_size=0, return_dict=False, **component_kwargs
        )
        self._outer = ma_cls(
            self.outer_n, buffer_size=0, return_dict=False, **component_kwargs
        )
        self._inner_component = Pyta2Component(self._inner)
        self._outer_component = Pyta2Component(self._outer)
        self.ma_type = str(self._inner.name)
        self.ma_kwargs = component_kwargs
        self.field = field
        self._inner_values: deque[float] = deque(maxlen=self._outer.required_window)
        super().__init__(
            window=self._inner.required_window + self._outer.required_window - 1,
            schema={"mean_of_mean": np.float64},
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        self._inner_component.reset()
        self._outer_component.reset()
        self._inner_values.clear()

    def forward(self, opens, highs, lows, closes, volumes) -> float:
        values = (opens, highs, lows, closes, volumes)[_FIELD_INDEX[self.field]]
        inner_value = self.apply_component(self._inner_component, values)
        if self._inner.g_index + 1 < self._inner.required_window:
            return float("nan")

        self._inner_values.append(float(inner_value))
        middle = np.fromiter(self._inner_values, dtype=np.float64)
        return float(self.apply_component(self._outer_component, middle))

    @property
    def full_name(self) -> str:
        return (
            f"mean_of_mean_v2({_component_full_name(self._inner)},"
            f"{_component_full_name(self._outer)})[{self.field}]"
        )

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info.update(
            {
                "field": self.field,
                "ma_type": self.ma_type,
                "ma_kwargs": dict(self.ma_kwargs),
                "inner_component": self._inner.meta_info,
                "outer_component": self._outer.meta_info,
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
) -> Any:
    """逐根重放 :class:`rKlineMeanOfMeanV2`。"""

    return forward_signal_apply(
        data,
        rKlineMeanOfMeanV2,
        param_args=(inner_n, outer_n),
        param_kwargs={
            "ma_type": ma_type,
            "field": field,
            "ma_kwargs": ma_kwargs,
        },
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineMeanOfMeanV2", "rKlineMeanOfMeanV2"]
