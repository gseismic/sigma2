from __future__ import annotations

import warnings


def warn_deprecated(old: str, replacement: str) -> None:
    """报告将在下一个破坏性版本删除的 K 线兼容入口。"""

    warnings.warn(
        f"{old} is deprecated; use {replacement}. It will be removed in sigma2 0.4.0.",
        DeprecationWarning,
        stacklevel=3,
    )


__all__ = ["warn_deprecated"]
