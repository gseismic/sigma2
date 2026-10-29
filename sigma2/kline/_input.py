from __future__ import annotations

from typing import Any


class _KlineStep:
    """单 K 线 Signal 和 Outcome 共用的固定输入。"""

    family = "kline"

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
        if not isinstance(is_missing, bool):
            raise TypeError("is_missing 必须是布尔值")
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
        return self._step(inputs, is_final=is_closed, observation_id=open_time)
