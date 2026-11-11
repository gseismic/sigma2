from sigma2.core.signal import rSignal

from ._input import _OrderBookStep


class rOrderBookSignal(_OrderBookStep, rSignal):
    """逐个处理订单簿快照。"""


__all__ = ["rOrderBookSignal"]
