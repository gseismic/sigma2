from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class _BundleStep:
    """不绑定 value 格式的多 symbol 输入入口。"""

    family = "bundle"
    input_schema_details = [
        {
            "name": "bundle",
            "type": "mapping",
            "description": "key 是 symbol 字符串，value 格式由具体算子定义",
            "values": {"type": "unknown"},
        },
        {"name": "time", "description": "时间标签，可为 None"},
    ]

    def step(self, bundle: Mapping[str, Any], *, time: Any = None) -> dict[str, Any]:
        return super().step(bundle, time=time)
