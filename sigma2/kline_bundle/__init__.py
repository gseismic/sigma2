"""多 symbol K 线截面的数据和计算。"""

from importlib import import_module
from typing import Any

from .data import KlineBundle

_MODULES = {
    "rKlineBundleSignal": "sigma2.core",
    "rKlineBundleOutcome": "sigma2.core",
    "rKlineBundleWindowSignal": "sigma2.core",
    "rKlineBundleWindowOutcome": "sigma2.core",
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
    """按需加载截面算子，避免数据类型和 core 的循环导入。"""
    if name not in _MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name = _MODULES[name]
    if module_name != "sigma2.core":
        module_name = f"{__name__}.{module_name}"
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value


__all__ = ["KlineBundle", *_MODULES]
