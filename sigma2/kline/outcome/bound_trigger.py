from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from typing import Any

from pyta2.effect import rFutureATRBoundTrigger

from sigma2.kline.outcome_base import rKlineOutcome

_MA_TYPES = frozenset({"SMA", "EMA", "WMA", "HMA", "DEMA", "TEMA", "ZLEMA"})


class _RetainedPrefix:
    """将有限历史呈现为 pyta2 按绝对下标访问的滚动前缀。"""

    def __init__(
        self, history: Sequence[tuple[float, ...]], length: int, field: int
    ) -> None:
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
    """使用锚点 ATR 扫描固定未来窗口的上下边界。"""

    name = "kline_atr_bound_trigger"

    def __init__(
        self,
        x_unit_ub: float,
        x_unit_lb: float,
        n_forward: int,
        *,
        atr_n: int = 20,
        atr_ma_type: str = "EMA",
        buffer_size: int = 1,
    ) -> None:
        if not isinstance(atr_ma_type, str):
            raise TypeError("atr_ma_type must be a string")
        atr_ma_type = atr_ma_type.strip().upper()
        if atr_ma_type not in _MA_TYPES:
            raise ValueError(f"unsupported single-parameter MA: {atr_ma_type}")
        effect = rFutureATRBoundTrigger(
            x_unit_ub,
            x_unit_lb,
            n_forward,
            n_atr=atr_n,
            atr_ma_type=atr_ma_type,
            buffer_size=0,
            return_dict=True,
        )
        super().__init__(
            schema=dict(effect.schema.items()),
            n_backward=effect.n_backward,
            n_forward=effect.n_forward,
            buffer_size=buffer_size,
            used_fields=("open", "high", "low", "close"),
        )
        self._state.update(
            effect=effect, history=deque(maxlen=max(2, self.n_forward + 1))
        )

    def forward(
        self,
        open,
        high,
        low,
        close,
        volume=None,
        *,
        open_time=None,
        is_closed=True,
        is_missing=False,
    ) -> dict[str, Any]:
        history = self._state["history"]
        history.append((open, high, low, close))
        retained = tuple(history)
        prefixes = tuple(
            _RetainedPrefix(retained, self.g_index + 1, i) for i in range(4)
        )
        return self._state["effect"].rolling(*prefixes)

    @property
    def x_unit_ub(self) -> float:
        return self._state["effect"].x_unit_ub

    @property
    def x_unit_lb(self) -> float:
        return self._state["effect"].x_unit_lb

    @property
    def atr_n(self) -> int:
        return self._state["effect"].n_atr

    @property
    def atr_ma_type(self) -> str:
        return self._state["effect"].atr_ma_type

    @property
    def full_name(self) -> str:
        return (
            f"{self.name}(x_unit_ub={self.x_unit_ub},x_unit_lb={self.x_unit_lb},"
            f"n_forward={self.n_forward},atr_n={self.atr_n},atr_ma_type={self.atr_ma_type})"
        )


__all__ = ["rKlineATRBoundTrigger"]
