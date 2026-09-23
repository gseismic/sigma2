"""sigma2 公共 API。"""

# 本地开发允许 pyta2 软链接布局，必须先执行导入路径兼容处理。
# ruff: noqa: E402

from .utils import ensure_pyta2_importable

ensure_pyta2_importable()

from pyta2.base.schema import Schema
from pyta2.utils.space import Box, Scalar, Space

from .core import (
    forward_signal_apply,
    pyta2_signal,
    rKlineSignal,
    rKlineWindowSignal,
    rOrderBookSignal,
    rPyta2Signal,
    rSignal,
    rTradeSignal,
)
from . import kline as _kline
from .kline import (
    KlineATR,
    KlineBoll,
    KlineGap,
    KlineKDJ,
    KlineMA,
    KlineMACD,
    KlineRSI,
    KlineReturn,
    rKlineATR,
    rKlineATRBoundTrigger,
    rKlineBoll,
    rKlineFutureChange,
    rKlineFutureHighLowChange,
    rKlineFutureReturn,
    rKlineGap,
    rKlineKDJ,
    rKlineMA,
    rKlineMACD,
    rKlineRSI,
    rKlineReturn,
)
from .orderbook import rBookSpread
from .trade import rTradeSignedVolume
from .utils import register_pyta2_indicator, resolve_pyta2_indicator

# 旧短名称保留为显式兼容属性，但不再进入 ``__all__``。
ATR = _kline.ATR
Boll = _kline.Boll
KDJ = _kline.KDJ
MA = _kline.MA
MACD = _kline.MACD
RSI = _kline.RSI
rATR = _kline.rATR
rBoll = _kline.rBoll
rGap = _kline.rGap
rKDJ = _kline.rKDJ
rMA = _kline.rMA
rMACD = _kline.rMACD
rPyta2SMA = _kline.rPyta2SMA
rReturn = _kline.rReturn
rRSI = _kline.rRSI
rSMA = _kline.rSMA

__all__ = [
    "Box",
    "KlineATR",
    "KlineBoll",
    "KlineGap",
    "KlineKDJ",
    "KlineMA",
    "KlineMACD",
    "KlineRSI",
    "KlineReturn",
    "Scalar",
    "Schema",
    "Space",
    "forward_signal_apply",
    "pyta2_signal",
    "register_pyta2_indicator",
    "resolve_pyta2_indicator",
    "rBookSpread",
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
    "rKlineSignal",
    "rKlineWindowSignal",
    "rOrderBookSignal",
    "rPyta2Signal",
    "rSignal",
    "rTradeSignal",
    "rTradeSignedVolume",
]
