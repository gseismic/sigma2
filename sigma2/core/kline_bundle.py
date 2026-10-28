from __future__ import annotations

from abc import abstractmethod
from collections import deque
from collections.abc import Sequence
from datetime import datetime
from typing import Any

import numpy as np
from pyta2.utils.validation import ensure_integer

from ._symbol_table import SymbolTable
from sigma2.kline_bundle.data import KlineBundle

from ._kline_data import normalize_symbols
from .signal import rOutcome, rSignal


class _KlineBundleInput:
    """校验共同时间轴，并为每 symbol 的结果提供固定输出轴。"""

    family = "kline_bundle"
    step_input_keys = ("bundle",)

    def __init__(
        self,
        schema: Any,
        *,
        symbols: Sequence[str],
        per_symbol: bool = True,
        **kwargs: Any,
    ) -> None:
        self.symbols = normalize_symbols(symbols)
        if not isinstance(per_symbol, bool):
            raise TypeError("per_symbol must be bool")
        self.per_symbol = per_symbol
        self._last_bar_time: datetime | None = None
        self._input_context: tuple[str, str] | None = None
        super().__init__(schema, **kwargs)

    def _new_output_table(self, maxlen: int | None) -> Any:
        if self.per_symbol:
            return SymbolTable(self.schema, self.symbols, maxlen, self.buffer_factor)
        return super()._new_output_table(maxlen)

    def step(self, bundle: KlineBundle) -> Any:
        self._ensure_healthy()
        if not isinstance(bundle, KlineBundle):
            raise TypeError("step requires a KlineBundle")
        if bundle.symbols != self.symbols:
            raise ValueError("bundle symbols and order must match the operator")
        context = (bundle.interval, bundle.time_label)
        if self._input_context is not None and context != self._input_context:
            raise ValueError("bundle interval and time_label must remain unchanged")
        if self._last_bar_time is not None and bundle.bar_time <= self._last_bar_time:
            raise ValueError("bundle bar_time must be strictly increasing")
        output = super().step(bundle)
        self._input_context = context
        self._last_bar_time = bundle.bar_time
        return output

    def reset(self) -> None:
        super().reset()
        self._last_bar_time = None
        self._input_context = None

    def missing_symbols(self) -> Any:
        """构造各 symbol 的缺失输出，沿用每个 Space 的哨兵。"""
        values = []
        for key in self.output_keys:
            space = self.schema[key]
            shape = (len(self.symbols), *tuple(getattr(space, "shape", ())))
            dtype = object if space.null_value is None else space.dtype
            values.append(np.full(shape, space.null_value, dtype=dtype))
        return values[0] if len(values) == 1 else tuple(values)

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info.update(
            {
                "symbols": self.symbols,
                "per_symbol": self.per_symbol,
                "last_bar_time": self._last_bar_time,
                "input_context": self._input_context,
            }
        )
        return info


class rKlineBundleSignal(_KlineBundleInput, rSignal):
    """每次处理一个 K 线截面，并计算当前时点的结果。"""


class rKlineBundleOutcome(_KlineBundleInput, rOutcome):
    """处理 K 线截面，结果等待固定后续快照后成熟。"""


class _KlineBundleWindow:
    """仅保留算法声明需要的快照窗口，与输出缓存分离。"""

    def __init__(self, *args: Any, history_window: int, **kwargs: Any) -> None:
        self._history_window = ensure_integer(
            history_window, "history_window", min_value=1
        )
        super().__init__(*args, **kwargs)

    def reset_extras(self) -> None:
        self._window: deque[KlineBundle] = deque(maxlen=self.history_window)
        self.reset_window_extras()

    def reset_window_extras(self) -> None:
        """子类可在此重置与输入窗口相关的状态。"""

    def _step_forward(self, bundle: KlineBundle) -> Any:
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


__all__ = [
    "rKlineBundleSignal",
    "rKlineBundleOutcome",
    "rKlineBundleWindowSignal",
    "rKlineBundleWindowOutcome",
]
