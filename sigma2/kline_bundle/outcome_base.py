from sigma2.core.outcome import rOutcome

from ._internal.input import _KlineBundleInput


class rKlineBundleOutcome(_KlineBundleInput, rOutcome):
    """处理 K 线截面，结果等待固定后续快照后成熟。"""


__all__ = ["rKlineBundleOutcome"]
