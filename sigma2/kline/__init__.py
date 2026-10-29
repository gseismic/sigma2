"""单 symbol K 线数据及相关计算。"""

from importlib import import_module
from typing import Any

_MODULES = {
    "KlineBar": "data",
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
    "KlineMACross": "trend",
    "KlineMA": "trend",
    "KlineMACD": "trend",
    "rKlineMA": "trend",
    "rKlineMACD": "trend",
    "rKlineMACross": "trend",
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
    "rKlineSignal": "signal",
    "rKlineOutcome": "outcome_base",
    "rKlineWindowSignal": "window",
    "rKlineWindowOutcome": "window",
    "pyta2_signal": "pyta2",
    "rPyta2Signal": "pyta2",
}


def __getattr__(name: str) -> Any:
    """按需加载对应模块中的算子。"""
    if name not in _MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f"{__name__}.{_MODULES[name]}"), name)
    globals()[name] = value
    return value


__all__ = list(_MODULES)
