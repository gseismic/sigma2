"""sigma2 公共 API；数据类型按需加载。"""

from importlib import import_module
from typing import Any

from pyta2.base.schema import Schema
from pyta2.utils.space import Box, Scalar, Space

from .core import qualify_factor_name, rOperator, rOutcome, rSignal

_GROUPS = {
    "batch": (
        "forward_outcome_apply",
        "forward_signal_apply",
    ),
    "kline": (
        "KlineBar",
        "KlineATR",
        "KlineBoll",
        "KlineGap",
        "KlineKDJ",
        "KlineMACD",
        "KlineMACross",
        "KlineMFI",
        "KlineOBV",
        "KlineVWAP",
        "KlineRSI",
        "KlineReturn",
        "rKlineATR",
        "rKlineATRBoundTrigger",
        "rKlineBoll",
        "rKlineFutureChange",
        "rKlineFutureHighLowChange",
        "rKlineFutureReturn",
        "rKlineGap",
        "rKlineKDJ",
        "rKlineMA",
        "rKlineMACD",
        "rKlineMACross",
        "rKlineMFI",
        "rKlineOBV",
        "rKlineVWAP",
        "rKlineRSI",
        "rKlineReturn",
        "rKlineSignal",
        "rKlineOutcome",
        "rKlineWindowSignal",
        "rKlineWindowOutcome",
        "pyta2_signal",
        "rPyta2Signal",
    ),
    "kline_bundle": (
        "KlineBundleFutureReturn",
        "KlineBundleMA",
        "KlineBundleRank",
        "KlineBundleReturnRank",
        "rKlineBundleMapOutcome",
        "rKlineBundleMapSignal",
        "rKlineBundleFutureReturn",
        "rKlineBundleMA",
        "rKlineBundleRank",
        "rKlineBundleReturnRank",
        "rKlineBundleSignal",
        "rKlineBundleOutcome",
        "rKlineBundleWindowSignal",
        "rKlineBundleWindowOutcome",
    ),
    "orderbook": ("rBookSpread", "rOrderBookSignal"),
    "trade": ("rTradeSignal", "rTradeSignedVolume"),
    "utils": ("register_pyta2_indicator", "resolve_pyta2_indicator"),
}
_MODULES = {name: module for module, names in _GROUPS.items() for name in names}


def __getattr__(name: str) -> Any:
    """访问公共名称时才导入相应数据模块。"""
    if name not in _MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f"{__name__}.{_MODULES[name]}"), name)
    globals()[name] = value
    return value


__all__ = [
    "Box",
    "Scalar",
    "Schema",
    "Space",
    "qualify_factor_name",
    "rOperator",
    "rOutcome",
    "rSignal",
    *_MODULES,
]
