from __future__ import annotations

from abc import abstractmethod
from collections import deque
from datetime import datetime
from typing import Any

import numpy as np
from pyta2.utils.validation import ensure_integer

from sigma2.kline.data import KlineBar
from .signal import rOutcome, rSignal


class _KlineInput:
    """约束单 symbol 输入流，避免不同品种共享递推状态。"""

    family = "kline"
    step_input_keys = ("bar",)

    def __init__(
        self, schema: Any, *, symbol: str | None = None, **kwargs: Any
    ) -> None:
        if symbol is not None and (not isinstance(symbol, str) or not symbol):
            raise ValueError("symbol must be a non-empty string or None")
        self.symbol = symbol
        self._bound_symbol = symbol
        self._last_bar_time: datetime | None = None
        super().__init__(schema, **kwargs)

    def step(self, bar: KlineBar) -> Any:
        self._ensure_healthy()
        if not isinstance(bar, KlineBar):
            raise TypeError("step requires a KlineBar")
        if self._bound_symbol is not None and bar.symbol != self._bound_symbol:
            raise ValueError("bar symbol must match the operator's input stream")
        if self._last_bar_time is not None and bar.bar_time <= self._last_bar_time:
            raise ValueError("bar_time must be strictly increasing")
        output = super().step(bar)
        self._bound_symbol = bar.symbol
        self._last_bar_time = bar.bar_time
        return output

    def reset(self) -> None:
        super().reset()
        self._bound_symbol = self.symbol
        self._last_bar_time = None

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info.update(
            {"symbol": self._bound_symbol, "last_bar_time": self._last_bar_time}
        )
        return info


class rKlineSignal(_KlineInput, rSignal):
    """处理单 symbol K 线，计算当前时点的结果。"""


class rKlineOutcome(_KlineInput, rOutcome):
    """处理单 symbol K 线，在固定后续步数后输出历史结果。"""


class _KlineWindow:
    """保存单 symbol 计算所需的有限 K 线历史。"""

    def __init__(self, *args: Any, history_window: int, **kwargs: Any) -> None:
        self._history_window = ensure_integer(
            history_window, "history_window", min_value=1
        )
        super().__init__(*args, **kwargs)

    def reset_extras(self) -> None:
        self._window: deque[KlineBar] = deque(maxlen=self.history_window)
        self.reset_window_extras()

    def reset_window_extras(self) -> None:
        """需要额外状态的子类可覆盖此钩子。"""

    def _step_forward(self, bar: KlineBar) -> Any:
        self._window.append(bar)
        fields = ("open", "high", "low", "close", "volume")
        arrays = tuple(
            np.asarray([getattr(item, field) for item in self._window], dtype=float)
            for field in fields
        )
        return self.forward(*arrays)

    @property
    def history_window(self) -> int:
        return self._history_window

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info["history_window"] = self.history_window
        return info

    @abstractmethod
    def forward(self, opens, highs, lows, closes, volumes) -> Any:
        """接收单 symbol 的一维历史字段数组。"""


class rKlineWindowSignal(_KlineWindow, rKlineSignal):
    """需要有限历史窗口的单 K 线 Signal。"""


class rKlineWindowOutcome(_KlineWindow, rKlineOutcome):
    """需要有限历史窗口的单 K 线 Outcome。"""


__all__ = ["rKlineSignal", "rKlineOutcome", "rKlineWindowSignal", "rKlineWindowOutcome"]
