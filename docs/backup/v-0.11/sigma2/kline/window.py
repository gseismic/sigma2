from __future__ import annotations

from abc import abstractmethod
from collections import deque
from collections.abc import Mapping
from typing import Any

import numpy as np
from pyta2.utils.validation import ensure_integer

from sigma2.kline.data import KlineBar

from ._internal.data import input_value, numeric_values
from .outcome_base import rKlineOutcome
from .signal import rKlineSignal


class _KlineWindow:
    """保存单 symbol 计算所需的有限 K 线历史。"""

    def __init__(self, *args: Any, history_window: int, **kwargs: Any) -> None:
        self._history_window = ensure_integer(
            history_window, "history_window", min_value=1
        )
        super().__init__(*args, **kwargs)

    def reset_extras(self) -> None:
        self._window: deque[Any] = deque(maxlen=self.history_window)
        self.reset_window_extras()

    def reset_window_extras(self) -> None:
        """需要额外状态的子类可覆盖此钩子。"""

    def _step_forward(self, bar: Mapping[str, Any] | KlineBar) -> Any:
        self._window.append(bar)
        fields = ("open", "high", "low", "close", "volume")
        arrays = tuple(
            numeric_values(
                [input_value(item, field, np.nan) for item in self._window],
                required=field != "volume" or "volume" in self.required_fields,
            )
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


__all__ = ["rKlineWindowSignal", "rKlineWindowOutcome"]
