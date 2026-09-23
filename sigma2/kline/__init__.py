"""K 线 Signal 公共 API。"""

from . import compat as _compat
from .momentum import KlineKDJ, KlineRSI, rKlineKDJ, rKlineRSI
from .price import KlineGap, KlineReturn, rKlineGap, rKlineReturn
from .target import (
    rKlineATRBoundTrigger,
    rKlineFutureChange,
    rKlineFutureHighLowChange,
    rKlineFutureReturn,
)
from .trend import KlineMA, KlineMACD, rKlineMA, rKlineMACD
from .volatility import KlineATR, KlineBoll, rKlineATR, rKlineBoll

# 旧短名称仍可显式导入一个兼容周期，但不再参与星号导入或 API 发现。
ATR = _compat.ATR
Boll = _compat.Boll
KDJ = _compat.KDJ
MA = _compat.MA
MACD = _compat.MACD
RSI = _compat.RSI
rATR = _compat.rATR
rBoll = _compat.rBoll
rGap = _compat.rGap
rKDJ = _compat.rKDJ
rMA = _compat.rMA
rMACD = _compat.rMACD
rPyta2SMA = _compat.rPyta2SMA
rReturn = _compat.rReturn
rRSI = _compat.rRSI
rSMA = _compat.rSMA

__all__ = [
    "KlineATR",
    "KlineBoll",
    "KlineGap",
    "KlineKDJ",
    "KlineMA",
    "KlineMACD",
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
    "rKlineRSI",
    "rKlineReturn",
]
