from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class _BundleStep:
    """不绑定 value 格式的多 symbol 输入入口。"""

    family = "bundle"
    input_schema_details = {
        "bundle": {
            "type": "mapping",
            "keys": {"type": "string"},
            "values": {"type": "unknown"},
        },
        "time": {"type": "unknown", "nullable": True},
    }

    def step(self, bundle: Mapping[str, Any], *, time: Any = None) -> dict[str, Any]:
        return super().step(bundle, time=time)
