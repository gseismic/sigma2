from sigma2.core.signal import rSignal

from ._input import _TradeStep


class rTradeSignal(_TradeStep, rSignal):
    """逐个处理成交事件。"""


__all__ = ["rTradeSignal"]
