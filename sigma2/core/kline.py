from __future__ import annotations

from abc import abstractmethod
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pyta2.utils.deque import DequeTable

from .signal import rSignal


class rKlineSignal(rSignal):
    """每次处理一根已确定 K 线的 signal family。"""

    family = "kline"
    step_input_keys = ("open", "high", "low", "close", "volume")

    def step(self, *, open: float, high: float, low: float, close: float, volume: float) -> Any:
        return super().step(open, high, low, close, volume)

    def update_last(
        self,
        *,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ) -> Any:
        return super().update_last(open, high, low, close, volume)

    @abstractmethod
    def forward(self, open: float, high: float, low: float, close: float, volume: float) -> Any:
        raise NotImplementedError


class rKlineWindowSignal(rKlineSignal):
    """显式选择维护 OHLCV 历史窗口的 K 线 signal。"""

    _update_state_fields = ()

    def __init__(self, *args: Any, history_window: int | None = None, **kwargs: Any) -> None:
        if history_window is not None and history_window <= 0:
            raise ValueError(
                f"history_window must be greater than 0, got {history_window}"
            )
        self._history_window = history_window
        super().__init__(*args, **kwargs)
        if history_window is not None and history_window < self.required_window:
            raise ValueError(
                "history_window must be greater than or equal to required_window "
                f"{self.required_window}, got {history_window}"
            )

    def reset_extras(self) -> None:
        self._window = DequeTable(
            maxlen=self.history_window,
            buffer_factor=self.buffer_factor,
            schema={
                "open": np.float64,
                "high": np.float64,
                "low": np.float64,
                "close": np.float64,
                "volume": np.float64,
            },
        )
        self.reset_window_extras()

    def reset_window_extras(self) -> None:
        """给需要 OHLCV 窗口以外状态的子类使用的可选 hook。"""

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
        return self.forward(
            self._window["open"],
            self._window["high"],
            self._window["low"],
            self._window["close"],
            self._window["volume"],
        )

    def _update_last_forward(
        self,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ) -> Any:
        self._window.update_row(
            -1,
            {
                "open": open,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            },
        )
        return self.forward(
            self._window["open"],
            self._window["high"],
            self._window["low"],
            self._window["close"],
            self._window["volume"],
        )

    @property
    def history_window(self) -> int:
        return self.required_window if self._history_window is None else self._history_window

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info["history_window"] = self.history_window
        return info

    @abstractmethod
    def forward(
        self,
        opens: NDArray[np.float64],
        highs: NDArray[np.float64],
        lows: NDArray[np.float64],
        closes: NDArray[np.float64],
        volumes: NDArray[np.float64],
    ) -> Any:
        raise NotImplementedError
