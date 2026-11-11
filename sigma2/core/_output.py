"""构造算子实例共用的输出字段、类型及缺失值配置。"""

from __future__ import annotations

from typing import Any

from pyta2.base.schema import Schema


def schema_storage(schema: Schema) -> tuple[dict[str, Any], dict[str, Any]]:
    """在构造时确定存储类型和缺失值，不复制 Space 的嵌套对象。"""
    dtypes = {}
    missing = {}
    for key, space in schema.items():
        null_value = space.null_value
        dtypes[key] = (
            space.dtype
            if null_value is not None and getattr(space, "shape", ()) == ()
            else object
        )
        missing[key] = null_value
    return dtypes, missing


def inferred_storage(result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """首次输出确定字段；不根据值推断存储类型。"""
    for key in result:
        if not isinstance(key, str):
            raise TypeError(f"forward() 输出字段必须是字符串，实际为 {key!r}")
    return dict.fromkeys(result, object), dict.fromkeys(result)
