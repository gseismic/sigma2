from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone


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
