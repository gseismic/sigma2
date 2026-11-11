from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class _KlineBundleStep:
    """多 symbol K 线截面的输入入口。"""

    family = "kline_bundle"
    input_schema_details = [
        {
            "name": "bundle",
            "type": "mapping",
            "description": "key 是 symbol 字符串，value 是该 symbol 的 K 线",
            "values": {
                "type": "mapping",
                "fields": [
                    {"name": "open", "type": "number"},
                    {"name": "high", "type": "number"},
                    {"name": "low", "type": "number"},
                    {"name": "close", "type": "number"},
                    {"name": "volume", "type": "number"},
                    {
                        "name": "is_missing",
                        "type": "bool",
                        "description": "具体含义由算子决定",
                    },
                ],
            },
        },
        {"name": "open_time", "description": "K 线截面开盘时间标签，可为 None"},
        {
            "name": "has_missing",
            "type": "bool",
            "description": "截面缺失标志，具体含义由算子决定",
        },
    ]

    def step(
        self,
        bundle: Mapping[str, Mapping[str, Any]],
        *,
        open_time: Any = None,
        has_missing: bool = False,
    ) -> dict[str, Any]:
        return super().step(bundle, open_time=open_time, has_missing=has_missing)
