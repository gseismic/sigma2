"""单 symbol K 线数据及相关计算。"""

from importlib import import_module
from typing import Any

from .data import KlineBar

_MODULES = {
    "KlineATR": "volatility",
    "KlineBoll": "volatility",
    "rKlineATR": "volatility",
    "rKlineBoll": "volatility",
    "KlineGap": "price",
    "KlineReturn": "price",
    "rKlineGap": "price",
    "rKlineReturn": "price",
    "KlineKDJ": "momentum",
    "KlineRSI": "momentum",
    "rKlineKDJ": "momentum",
    "rKlineRSI": "momentum",
    "KlineMA": "trend",
    "KlineMACD": "trend",
    "KlineMACross": "trend",
    "KlineMeanOfMean": "trend",
    "KlineMeanOfMeanV2": "trend",
    "rKlineMA": "trend",
    "rKlineMACD": "trend",
    "rKlineMACross": "trend",
    "rKlineMeanOfMean": "trend",
    "rKlineMeanOfMeanV2": "trend",
    "KlineOBV": "volume",
    "KlineMFI": "volume",
    "KlineVWAP": "volume",
    "rKlineOBV": "volume",
    "rKlineMFI": "volume",
    "rKlineVWAP": "volume",
    "rKlineATRBoundTrigger": "outcome",
    "rKlineFutureChange": "outcome",
    "rKlineFutureHighLowChange": "outcome",
    "rKlineFutureReturn": "outcome",
    "rKlineSignal": "sigma2.core",
    "rKlineOutcome": "sigma2.core",
    "rKlineWindowSignal": "sigma2.core",
    "rKlineWindowOutcome": "sigma2.core",
}


def __getattr__(name: str) -> Any:
    """按需加载算子，避免数据类型与 core 初始化相互依赖。"""
    if name not in _MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name = _MODULES[name]
    if module_name != "sigma2.core":
        module_name = f"{__name__}.{module_name}"
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value


__all__ = ["KlineBar", *_MODULES]
