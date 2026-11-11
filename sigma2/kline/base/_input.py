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
        is_missing=False,
    ) -> dict[str, Any]:
        return super().step(
            open,
            high,
            low,
            close,
            volume,
            open_time=open_time,
            is_missing=is_missing,
        )
