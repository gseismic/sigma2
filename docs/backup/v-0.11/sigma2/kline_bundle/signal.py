from sigma2.core.signal import rSignal

from ._internal.input import _KlineBundleInput


class rKlineBundleSignal(_KlineBundleInput, rSignal):
    """每次处理一个 K 线截面，并计算当前时点的结果。"""


__all__ = ["rKlineBundleSignal"]
