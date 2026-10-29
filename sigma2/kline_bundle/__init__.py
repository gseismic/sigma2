"""多 symbol K 线截面的数据和计算。"""

from importlib import import_module
from typing import Any

_MODULES = {
    "rKlineBundleSignal": "signal",
    "rKlineBundleOutcome": "outcome_base",
    "rKlineBundleWindowSignal": "window",
    "rKlineBundleWindowOutcome": "window",
    "rKlineBundleMapSignal": "map",
    "rKlineBundleMapOutcome": "map",
    "KlineBundleRank": "cross_section",
    "rKlineBundleRank": "cross_section",
    "KlineBundleReturnRank": "cross_section",
    "rKlineBundleReturnRank": "cross_section",
    "KlineBundleMA": "trend",
    "rKlineBundleMA": "trend",
    "KlineBundleFutureReturn": "outcome",
    "rKlineBundleFutureReturn": "outcome",
}


def __getattr__(name: str) -> Any:
    """按需加载对应模块中的截面算子。"""
    if name not in _MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f"{__name__}.{_MODULES[name]}"), name)
    globals()[name] = value
    return value


__all__ = list(_MODULES)
