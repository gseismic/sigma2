from __future__ import annotations

from typing import Any

from sigma2.core.signal import rSignal


class rKlineSignal(rSignal):
    """单 symbol K 线算子：未结束的最后一根可以重复更新。"""

    family = "kline"
    step_input_keys = (
        "open",
        "high",
        "low",
        "close",
        "volume",
        "open_time",
        "is_closed",
        "is_missing",
    )

    def __init__(
        self, schema: Any, *, symbol: str | None = None, **kwargs: Any
    ) -> None:
        self.symbol = symbol
        self._unfinished = False
        self._unfinished_time = None
        kwargs.setdefault("scope", symbol)
        super().__init__(schema, **kwargs)

    def step(
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
        self._ensure_healthy()
        if self._unfinished and open_time != self._unfinished_time:
            raise ValueError("the previous K-line is not closed")

        if is_missing:
            open = high = low = close = volume = float("nan")
        inputs = {
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "open_time": open_time,
            "is_closed": is_closed,
            "is_missing": is_missing,
        }
        if self._unfinished:
            result = self._replace_last(**inputs)
        else:
            result = self._advance(not is_closed, **inputs)

        self._unfinished = not is_closed
        self._unfinished_time = None if is_closed else open_time
        if is_closed:
            self._clear_checkpoint()
        return result

    def reset(self) -> None:
        super().reset()
        self._unfinished = False
        self._unfinished_time = None


__all__ = ["rKlineSignal"]
