from sigma2.core.outcome import rOutcome

from ._input import _KlineStep


class rKlineOutcome(_KlineStep, rOutcome):
    """处理单 symbol K 线，在固定后续步数后输出历史结果。"""


__all__ = ["rKlineOutcome"]
