"""按需导出 K 线趋势算子。"""

from importlib import import_module
from typing import Any

_MODULES = {
    "rKlineMA": "ma",
    "rKlineMACD": "macd",
    "KlineMACross": "cross",
    "rKlineMACross": "cross",
}


def __getattr__(name: str) -> Any:
    if name not in _MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f"{__name__}.{_MODULES[name]}"), name)
    globals()[name] = value
    return value


__all__ = list(_MODULES)
