from sigma2.core.signal import rSignal

from ._input import _KlineStep


class rKlineSignal(_KlineStep, rSignal):
    """处理一条 symbol 的 K 线序列，支持更新未结束的最后一根。"""


__all__ = ["rKlineSignal"]
