from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

import numpy as np

OHLC_FIELDS = ("open", "high", "low", "close")


def normalize_key_map(value: Mapping[str, str] | None, name: str) -> dict[str, str]:
    """验证逻辑字段到原始输入字段的映射，并复制调用方配置。"""
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping or None")
    result = dict(value)
    if any(
        not isinstance(key, str) or not key or not isinstance(source, str) or not source
        for key, source in result.items()
    ):
        raise ValueError(f"{name} must map non-empty field names to field names")
    return result


def normalize_field_names(fields: Sequence[str] | None, name: str) -> tuple[str, ...]:
    """验证字段名列表并按原顺序去重。"""
    if fields is None:
        fields = ()
    if isinstance(fields, (str, bytes)):
        raise TypeError(f"{name} must be a sequence of field names")
    result = tuple(fields)
    if any(not isinstance(field, str) or not field for field in result):
        raise ValueError(f"{name} must contain non-empty field names")
    return tuple(dict.fromkeys(result))


def normalize_required_fields(fields: Sequence[str] | None) -> tuple[str, ...]:
    """合并 K 线基础字段和算子声明的其他必需字段。"""
    result = normalize_field_names(fields, "required_fields")
    return tuple(dict.fromkeys((*OHLC_FIELDS, *result)))


def include_required_fields(kwargs: dict[str, Any], *fields: str) -> None:
    """将算法依赖加入调用方为自定义算子声明的输入字段。"""
    configured = normalize_required_fields(kwargs.pop("required_fields", ()))
    kwargs["required_fields"] = tuple(dict.fromkeys((*configured, *fields)))


class FieldView(Mapping[str, Any]):
    """保留额外键，并以逻辑字段读取一份原始输入快照。"""

    def __init__(
        self,
        raw: Mapping[str, Any],
        key_map: Mapping[str, str],
        *,
        snapshot_fields: Sequence[str] = (),
    ) -> None:
        self._raw = dict(raw)
        self._key_map = dict(key_map)
        for field in snapshot_fields:
            source = self._key_map.get(field, field)
            if source in self._raw:
                try:
                    self._raw[source] = deepcopy(self._raw[source])
                except Exception:
                    # 无法复制的自定义对象仍可用于即时计算，持有时由算子自行管理。
                    pass
        keys = dict.fromkeys((*self._raw, *self._key_map))
        self._keys = tuple(
            key for key in keys if self._key_map.get(key, key) in self._raw
        )

    def __getitem__(self, key: str) -> Any:
        return self._raw[self._key_map.get(key, key)]

    def __iter__(self) -> Iterator[str]:
        return iter(self._keys)

    def __len__(self) -> int:
        return len(self._keys)

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def require_fields(data: Mapping[str, Any] | Any, fields: Sequence[str]) -> None:
    """在生命周期推进前检查必需字段。"""
    if isinstance(data, Mapping):
        missing = [field for field in fields if field not in data]
    else:
        missing = [field for field in fields if not hasattr(data, field)]
    if missing:
        raise KeyError(f"input is missing required fields: {missing}")


def input_value(data: Mapping[str, Any] | Any, field: str, default: Any = None) -> Any:
    """从字典视图或保留兼容的旧数据对象读取字段。"""
    if isinstance(data, Mapping):
        return data.get(field, default)
    return getattr(data, field, default)


def numeric_values(values: Sequence[Any], *, required: bool) -> np.ndarray:
    """仅在算法不依赖该字段时，把无法转换的可选值当作缺失值。"""
    try:
        result = np.asarray(values, dtype=float)
        if result.ndim != 1:
            raise ValueError("each K-line field value must be a scalar")
        return result
    except (TypeError, ValueError, OverflowError):
        if required:
            raise
        converted = []
        for value in values:
            try:
                converted.append(float(value))
            except (TypeError, ValueError, OverflowError):
                converted.append(np.nan)
        return np.asarray(converted, dtype=float)


def utc_time(value: datetime, name: str) -> datetime:
    """要求输入明确时区，统一时间表示以便跨数据源对齐。"""
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must have an explicit timezone")
    return value.astimezone(timezone.utc)


def normalize_symbols(symbols: Sequence[str]) -> tuple[str, ...]:
    """固定 symbol 顺序，避免截面和结果位置发生静默错位。"""
    if isinstance(symbols, (str, bytes)):
        raise TypeError("symbols must be a sequence of symbol strings")
    result = tuple(symbols)
    if any(not isinstance(symbol, str) or not symbol for symbol in result):
        raise ValueError("symbols must contain non-empty strings")
    if len(set(result)) != len(result):
        raise ValueError("symbols must be unique")
    return result
