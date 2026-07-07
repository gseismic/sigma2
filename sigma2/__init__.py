"""sigma2 公共 API。"""

from .utils import ensure_pyta2_importable

ensure_pyta2_importable()

from pyta2.base.schema import Schema
from pyta2.utils.space import Box, Scalar, Space

from .core import (
    pyta2_signal,
    rKlineSignal,
    rKlineWindowSignal,
    rOrderBookSignal,
    rPyta2Signal,
    rSignal,
    rTradeSignal,
)
from .kline import rGap, rPyta2SMA, rReturn, rSMA
from .orderbook import rBookSpread
from .trade import rTradeSignedVolume
from .utils import register_pyta2_indicator, resolve_pyta2_indicator

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
