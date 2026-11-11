from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class _KlineBundleStep:
    """多 symbol K 线截面的输入入口。"""

    family = "kline_bundle"
    input_schema_details = {
        "bundle": {
            "type": "mapping",
            "keys": {"type": "string"},
            "values": {
                "type": "object",
                "fields": {
                    **{
                        field: {
                            "required": False,
                            "schema": {"type": "number", "nullable": True},
                        }
                        for field in ("open", "high", "low", "close", "volume")
                    },
                    "is_missing": {
                        "required": False,
                        "schema": {"type": "boolean"},
                    },
                },
                "allow_extra": True,
            },
        },
        "open_time": {"type": "unknown", "nullable": True},
        "has_missing": {"type": "boolean"},
    }

    def step(
        self,
        bundle: Mapping[str, Mapping[str, Any]],
        *,
        open_time: Any = None,
        has_missing: bool = False,
    ) -> dict[str, Any]:
        return super().step(bundle, open_time=open_time, has_missing=has_missing)
