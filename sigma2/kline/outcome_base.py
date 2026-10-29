from sigma2.core.outcome import rOutcome

from ._internal.input import _KlineInput


class rKlineOutcome(_KlineInput, rOutcome):
    """处理单 symbol K 线，在固定后续步数后输出历史结果。"""


__all__ = ["rKlineOutcome"]
