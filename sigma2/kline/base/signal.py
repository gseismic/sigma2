from sigma2.core.signal import rSignal

from ._input import _KlineStep


class rKlineSignal(_KlineStep, rSignal):
    """逐根处理一条 symbol 的 K 线序列。"""


__all__ = ["rKlineSignal"]
