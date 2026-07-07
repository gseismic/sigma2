from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sigma2.utils.pyta2 import (
    ensure_pyta2_importable,
    normalize_pyta2_inputs,
    resolve_pyta2_default_inputs,
    resolve_pyta2_indicator,
)

from .kline import rKlineWindowSignal

ensure_pyta2_importable()


def pyta2_signal(
    indicator: str | type,
    *,
    params: dict[str, Any] | None = None,
    field: str | None = None,
    inputs: Sequence[str] | None = None,
    **kwargs: Any,
) -> "rPyta2Signal":
    """用名称或 class 快捷构造 pyta2 适配信号。"""

    return rPyta2Signal(
        indicator,
        params=params,
        field=field,
        inputs=inputs,
        **kwargs,
    )


class rPyta2Signal(rKlineWindowSignal):
    """把 pyta2 rolling indicator 适配成标准 K 线 step signal。"""

    family = "kline"

    def __init__(
        self,
        indicator: str | type,
        *,
        params: dict[str, Any] | None = None,
        field: str | None = None,
        inputs: Sequence[str] | None = None,
        full_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        if field is not None and inputs is not None:
            raise ValueError("field and inputs cannot both be provided")

        self.indicator_name = indicator if isinstance(indicator, str) else indicator.__name__
        self.indicator_cls = resolve_pyta2_indicator(indicator)
        self.indicator_params = dict(params or {})
        self.inputs = self._resolve_inputs(indicator, field=field, inputs=inputs)
        self._full_name = full_name
        self._indicator = self._make_indicator()

        super().__init__(
            window=self._indicator.window,
            schema=self._indicator.schema,
            extra_window=self._indicator.extra_window,
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        self._indicator = self._make_indicator()

    def _step_forward(
        self,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ) -> Any:
        self._window.append(
            {
                "open": open,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
        return self._indicator.rolling(*self._indicator_args_from_window())

    def forward(self, opens, highs, lows, closes, volumes) -> Any:
        temp_indicator = self._make_indicator()
        values = self._indicator_args_from_arrays(opens, highs, lows, closes, volumes)
        return temp_indicator.rolling(*values)

    @property
    def full_name(self) -> str:
        if self._full_name is not None:
            return self._full_name
        return f"{self._indicator.full_name}[{','.join(self.inputs)}]"

    def _make_indicator(self):
        params = dict(self.indicator_params)
        params.setdefault("buffer_size", 1)
        params["return_dict"] = False
        return self.indicator_cls(**params)

    def _indicator_args_from_window(self) -> tuple[Any, ...]:
        arrays = {
            "open": self._window["open"],
            "high": self._window["high"],
            "low": self._window["low"],
            "close": self._window["close"],
            "volume": self._window["volume"],
        }
        return tuple(arrays[field] for field in self.inputs)

    def _indicator_args_from_arrays(
        self,
        opens,
        highs,
        lows,
        closes,
        volumes,
    ) -> tuple[Any, ...]:
        arrays = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }
        return tuple(arrays[field] for field in self.inputs)

    def _resolve_inputs(
        self,
        indicator: str | type,
        *,
        field: str | None,
        inputs: Sequence[str] | None,
    ) -> tuple[str, ...]:
        if field is not None:
            return normalize_pyta2_inputs((field,))
        if inputs is not None:
            return normalize_pyta2_inputs(inputs)
        default_inputs = resolve_pyta2_default_inputs(indicator)
        if default_inputs is not None:
            return default_inputs
        return ("close",)
