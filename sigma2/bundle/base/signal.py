from sigma2.core.signal import rSignal

from ._input import _BundleStep


class rBundleSignal(_BundleStep, rSignal):
    """逐步处理多 symbol 输入；value 格式由具体算子定义。"""


__all__ = ["rBundleSignal"]
