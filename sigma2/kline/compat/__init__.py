"""0.3.x 兼容入口；计划在 0.4.0 删除。"""

from .atr import ATR, rATR
from .boll import Boll, rBoll
from .gap import rGap
from .kdj import KDJ, rKDJ
from .ma import MA, rMA
from .macd import MACD, rMACD
from .pyta2_sma import rPyta2SMA
from .return_ import rReturn
from .rsi import RSI, rRSI
from .sma import rSMA

__all__ = [
    "ATR",
    "Boll",
    "KDJ",
    "MA",
    "MACD",
    "RSI",
    "rATR",
    "rBoll",
    "rGap",
    "rKDJ",
    "rMA",
    "rMACD",
    "rPyta2SMA",
    "rRSI",
    "rReturn",
    "rSMA",
]
