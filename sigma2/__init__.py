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
from .kline import (
    ATR,
    Boll,
    KDJ,
    MA,
    MACD,
    RSI,
    rATR,
    rBoll,
    rGap,
    rKDJ,
    rKlineATRBoundTrigger,
    rKlineFutureChange,
    rKlineFutureHighLowChange,
    rKlineFutureReturn,
    rMA,
    rMACD,
    rPyta2SMA,
    rRSI,
    rReturn,
    rSMA,
)
from .orderbook import rBookSpread
from .trade import rTradeSignedVolume
from .utils import register_pyta2_indicator, resolve_pyta2_indicator

__all__ = [
    "ATR",
    "Boll",
    "Box",
    "KDJ",
    "MA",
    "MACD",
    "RSI",
    "Scalar",
    "Schema",
    "Space",
    "forward_signal_apply",
    "pyta2_signal",
    "register_pyta2_indicator",
    "resolve_pyta2_indicator",
    "rBookSpread",
    "rATR",
    "rBoll",
    "rGap",
    "rKDJ",
    "rKlineATRBoundTrigger",
    "rKlineFutureChange",
    "rKlineFutureHighLowChange",
    "rKlineFutureReturn",
    "rKlineSignal",
    "rKlineWindowSignal",
    "rMA",
    "rMACD",
    "rOrderBookSignal",
    "rPyta2Signal",
    "rPyta2SMA",
    "rReturn",
    "rRSI",
    "rSMA",
    "rSignal",
    "rTradeSignal",
    "rTradeSignedVolume",
]
