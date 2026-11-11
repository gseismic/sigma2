from __future__ import annotations

from typing import Any


class _KlineStep:
    """单 K 线 Signal 和 Outcome 共用的固定输入。"""

    family = "kline"
    input_schema_details = [
        {"name": "open", "type": "number"},
        {"name": "high", "type": "number"},
        {"name": "low", "type": "number"},
        {"name": "close", "type": "number"},
        {"name": "volume", "type": "number", "description": "可为 None"},
        {"name": "open_time", "description": "K 线开盘时间标签，可为 None"},
        {"name": "is_missing", "type": "bool", "description": "缺失标志，原样传给算子"},
    ]

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
