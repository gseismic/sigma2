from sigma2.core.signal import rSignal

from ._input import _KlineBundleStep


class rKlineBundleSignal(_KlineBundleStep, rSignal):
    """处理同一周期的多 symbol K 线截面。"""


__all__ = ["rKlineBundleSignal"]
