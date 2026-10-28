from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from pyta2.base import rIndicator

from sigma2.utils.pyta2 import normalize_pyta2_inputs

from ._kline_data import include_required_fields
from .kline import rKlineWindowSignal


def rolling_with_nan_recovery(indicator: rIndicator, *values: Any) -> Any:
    """防止当前 pyta2 KAMA 在无效窗口后持续保留 NaN 递推状态。"""
    if indicator.name == "KAMA" and any(
        not np.all(np.isfinite(value)) for value in values
    ):
        indicator.reset()
        return indicator.missing_output
    return indicator.rolling(*values)


class _rKlineIndicatorFactor(rKlineWindowSignal):
    """把单 symbol K 线整理为 pyta2 指标需要的历史序列。"""

    def __init__(
        self,
        indicator: rIndicator,
        *,
        fields: Sequence[str],
        history_window: int | None = None,
        **kwargs: Any,
    ) -> None:
        if not isinstance(indicator, rIndicator):
            raise TypeError("indicator must be a pyta2 rIndicator")
        if not fields:
            raise ValueError("fields must contain at least one K-line field")
        self.fields = normalize_pyta2_inputs(fields)
        self._indicator = indicator
        self._indicator.resize_buffer(0)
        self._indicator.return_dict = False
        if history_window is None:
            history_window = indicator.min_periods
        include_required_fields(kwargs, *self.fields)
        super().__init__(
            indicator.schema,
            n_backward=indicator.n_backward,
            history_window=history_window,
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        self._indicator.reset()

    def forward(self, opens, highs, lows, closes, volumes) -> Any:
        arrays = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }
        inputs = tuple(arrays[field] for field in self.fields)
        return rolling_with_nan_recovery(self._indicator, *inputs)

    @property
    def full_name(self) -> str:
        return f"{self._indicator.full_name}[{','.join(self.fields)}]"

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info.update({"fields": self.fields, "component": self._indicator.meta_info})
        return info


__all__ = ["_rKlineIndicatorFactor"]
