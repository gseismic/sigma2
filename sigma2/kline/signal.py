from sigma2.core.signal import rSignal

from ._internal.input import _KlineInput


class rKlineSignal(_KlineInput, rSignal):
    """处理单 symbol K 线，计算当前时点的结果。"""


__all__ = ["rKlineSignal"]
