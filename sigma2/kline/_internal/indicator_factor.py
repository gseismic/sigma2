from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pyta2.base import rIndicator

from sigma2.core import rKlineWindowSignal
from sigma2.utils.pyta2 import normalize_pyta2_inputs


class _rKlineIndicatorFactor(rKlineWindowSignal):
    """由单个 pyta2 rolling component 支撑的 K 线因子内部模板。"""

    _update_state_fields = ()

    def __init__(
        self,
        indicator: rIndicator,
        *,
        fields: Sequence[str],
        history_window: int | None = None,
        **kwargs: Any,
    ) -> None:
        if not isinstance(indicator, rIndicator):
            raise TypeError(
                "indicator must be a pyta2 rIndicator instance, "
                f"got {type(indicator)}"
            )
        if not fields:
            raise ValueError("fields must contain at least one K-line field")

        self.fields = normalize_pyta2_inputs(fields)
        self._indicator = indicator
        self._indicator.resize_buffer(0)
        self._indicator.return_dict = False

        minimum_history = indicator.required_window
        if history_window is not None and history_window < minimum_history:
            raise ValueError(
                "history_window must be greater than or equal to the component "
                f"required_window {minimum_history}, got {history_window}"
            )
        super().__init__(
            window=indicator.window,
            schema=indicator.schema,
            extra_window=indicator.extra_window,
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
        values = tuple(arrays[field] for field in self.fields)
        return self._apply_pyta2(self._indicator, *values)

    @property
    def full_name(self) -> str:
        return f"{self._indicator.full_name}[{','.join(self.fields)}]"

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info.update(
            {
                "fields": self.fields,
                "component": self._indicator.meta_info,
            }
        )
        return info


__all__ = ["_rKlineIndicatorFactor"]
