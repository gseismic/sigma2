"""0.3.x 内部兼容路径；新实现位于 ``kline._internal``。"""

from ._internal.indicator_factor import _rKlineIndicatorFactor

__all__ = ["_rKlineIndicatorFactor"]
