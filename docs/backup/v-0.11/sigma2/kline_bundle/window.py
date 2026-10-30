from __future__ import annotations

from abc import abstractmethod
from collections import deque
from collections.abc import Mapping
from typing import Any

import numpy as np
from pyta2.utils.validation import ensure_integer

from .outcome_base import rKlineBundleOutcome
from .signal import rKlineBundleSignal


class _KlineBundleWindow:
    """仅保留算法声明需要的快照窗口，与输出缓存分离。"""

    def __init__(self, *args: Any, history_window: int, **kwargs: Any) -> None:
        self._history_window = ensure_integer(
            history_window, "history_window", min_value=1
        )
        super().__init__(*args, **kwargs)

    def reset_extras(self) -> None:
        self._window: deque[Any] = deque(maxlen=self.history_window)
        self.reset_window_extras()

    def reset_window_extras(self) -> None:
        """子类可在此重置与输入窗口相关的状态。"""

    def _step_forward(self, bundle: Mapping[str, Any]) -> Any:
        self._window.append(bundle)
        fields = ("open", "high", "low", "close", "volume")
        arrays = tuple(
            np.stack([item.field(field) for item in self._window], axis=0)
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
        """接收形状为 (历史时点, symbol) 的字段数组。"""


class rKlineBundleWindowSignal(_KlineBundleWindow, rKlineBundleSignal):
    """需要有限 K 线历史的 Signal。"""


class rKlineBundleWindowOutcome(_KlineBundleWindow, rKlineBundleOutcome):
    """需要有限 K 线历史的 Outcome。"""


__all__ = ["rKlineBundleWindowSignal", "rKlineBundleWindowOutcome"]
