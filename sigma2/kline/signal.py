from __future__ import annotations

from typing import Any

from sigma2.core.signal import rSignal


class rKlineSignal(rSignal):
    """处理一条 symbol 的 K 线序列，支持更新未结束的最后一根。"""

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


__all__ = ["rKlineSignal"]
