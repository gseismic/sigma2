from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sigma2.core.signal import rSignal


class rKlineBundleSignal(rSignal):
    """处理同一时点的多 symbol K 线截面。"""

    family = "kline_bundle"

    def step(
        self,
        bundle: Mapping[str, Mapping[str, Any]],
        *,
        open_time: Any = None,
        has_missing: bool = False,
    ) -> dict[str, Any]:
        return super().step(bundle, open_time=open_time, has_missing=has_missing)


__all__ = ["rKlineBundleSignal"]
