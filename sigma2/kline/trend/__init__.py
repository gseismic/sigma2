"""按需导出 K 线趋势算子。"""

from importlib import import_module
from typing import Any

_MODULES = {
    "KlineMA": "ma",
    "rKlineMA": "ma",
    "KlineMACD": "macd",
    "rKlineMACD": "macd",
    "KlineMACross": "cross",
    "rKlineMACross": "cross",
    "KlineMeanOfMean": "mean_of_mean",
    "rKlineMeanOfMean": "mean_of_mean",
    "KlineMeanOfMeanV2": "mean_of_mean_v2",
    "rKlineMeanOfMeanV2": "mean_of_mean_v2",
}


def __getattr__(name: str) -> Any:
    if name not in _MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f"{__name__}.{_MODULES[name]}"), name)
    globals()[name] = value
    return value


__all__ = list(_MODULES)
