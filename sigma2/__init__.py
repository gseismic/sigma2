"""sigma2 公共 API。"""

from ._pyta2 import ensure_pyta2_importable

ensure_pyta2_importable()

from pyta2.base.schema import Schema
from pyta2.utils.space import Box, Scalar, Space

from .adapters import (
    pyta2_signal,
    register_pyta2_indicator,
    resolve_pyta2_indicator,
    rPyta2Signal,
    rPyta2SMA,
)
from .base import rSignal
from .families import rKlineSignal, rKlineWindowSignal, rOrderBookSignal, rTradeSignal
from .signals import rBookSpread, rGap, rReturn, rSMA, rTradeSignedVolume

__all__ = [
    "Box",
    "Scalar",
    "Schema",
    "Space",
    "pyta2_signal",
    "register_pyta2_indicator",
    "resolve_pyta2_indicator",
    "rBookSpread",
    "rGap",
    "rKlineSignal",
    "rKlineWindowSignal",
    "rOrderBookSignal",
    "rPyta2Signal",
    "rPyta2SMA",
    "rReturn",
    "rSMA",
    "rSignal",
    "rTradeSignal",
    "rTradeSignedVolume",
]
