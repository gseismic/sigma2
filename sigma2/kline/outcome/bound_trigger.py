from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from typing import Any

from pyta2.effect import rFutureATRBoundTrigger

from sigma2.core import rKlineOutcome
from sigma2.core._kline_data import input_value, numeric_values


class _RetainedPrefix:
    """将有限历史呈现为 pyta2 按绝对下标访问的滚动前缀。"""

    def __init__(self, history: Sequence[tuple[float, ...]], length: int, field: int) -> None:
        self._history, self._length, self._field = history, length, field

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, index: int) -> float:
        if index < 0:
            index += self._length
        relative = index - (self._length - len(self._history))
        if index < 0 or relative < 0 or relative >= len(self._history):
            raise IndexError("requested observation is outside retained history")
        return self._history[relative][self._field]


class rKlineATRBoundTrigger(rKlineOutcome):
    """复用 pyta2 的固定未来窗口 ATR 边界扫描。"""

    name = "kline_atr_bound_trigger"

    def __init__(
        self, x_unit_ub: float, x_unit_lb: float, n_forward: int, *,
        symbol: str | None = None, atr_n: int = 20,
        atr_ma_type: str = "EMA", **kwargs: Any,
    ) -> None:
        self._effect = rFutureATRBoundTrigger(
            x_unit_ub, x_unit_lb, n_forward, n_atr=atr_n,
            atr_ma_type=atr_ma_type, buffer_size=0, return_dict=False,
        )
        self.x_unit_ub, self.x_unit_lb = self._effect.x_unit_ub, self._effect.x_unit_lb
        self.atr_n, self.atr_ma_type = self._effect.n_atr, self._effect.atr_ma_type
        super().__init__(
            schema=self._effect.schema, symbol=symbol,
            n_backward=self._effect.n_backward, n_forward=self._effect.n_forward,
            **kwargs,
        )

    def reset_extras(self) -> None:
        self._effect.reset()
        self._history: deque[tuple[float, ...]] = deque(maxlen=max(2, self.n_forward + 1))

    def forward(self, bar):
        fields = ("open", "high", "low", "close")
        values = numeric_values([input_value(bar, field) for field in fields], required=True)
        self._history.append(tuple(values))
        history = tuple(self._history)
        prefixes = tuple(
            _RetainedPrefix(history, self.g_index + 1, index)
            for index in range(len(fields))
        )
        return self._effect.rolling(*prefixes)

    @property
    def full_name(self) -> str:
        return (
            f"{self.name}(x_unit_ub={self.x_unit_ub},x_unit_lb={self.x_unit_lb},"
            f"n_forward={self.n_forward},atr_n={self.atr_n},atr_ma_type={self.atr_ma_type})"
        )


__all__ = ["rKlineATRBoundTrigger"]
