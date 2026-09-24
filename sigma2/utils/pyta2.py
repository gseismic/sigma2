from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from pyta2.base import rIndicator

IndicatorResolver = type | Callable[[], type]

_FIELD_ALIASES = {
    "open": "open",
    "opens": "open",
    "high": "high",
    "highs": "high",
    "low": "low",
    "lows": "low",
    "close": "close",
    "closes": "close",
    "volume": "volume",
    "volumes": "volume",
}

_PYTA2_REGISTRY: dict[str, tuple[IndicatorResolver, tuple[str, ...]]] = {}


class Pyta2Component:
    """把 pyta2 指标适配成 Signal 的 step/update_last 子组件。"""

    def __init__(self, indicator: rIndicator) -> None:
        if not isinstance(indicator, rIndicator):
            raise TypeError(
                f"indicator must be a pyta2 rIndicator instance, got {type(indicator)}"
            )
        self.indicator = indicator

    def step(self, *args: Any, **kwargs: Any) -> Any:
        return self.indicator.rolling(*args, **kwargs)

    def update_last(self, *args: Any, **kwargs: Any) -> Any:
        return self.indicator.update_last(*args, **kwargs)

    def reset(self) -> None:
        self.indicator.reset()


def register_pyta2_indicator(
    name: str,
    indicator: IndicatorResolver,
    *,
    default_inputs: Sequence[str] = ("close",),
) -> None:
    """注册 pyta2 rolling indicator 名称映射。"""

    key = _normalize_indicator_name(name)
    _PYTA2_REGISTRY[key] = (indicator, normalize_pyta2_inputs(default_inputs))


def resolve_pyta2_indicator(indicator: str | type) -> type:
    """把 pyta2 指标名或 class 解析为 rolling indicator class。"""

    if isinstance(indicator, type):
        return indicator
    if not isinstance(indicator, str):
        raise TypeError(f"indicator must be str or class, got {type(indicator)}")

    key = _normalize_indicator_name(indicator)
    if key in _PYTA2_REGISTRY:
        resolver, _ = _PYTA2_REGISTRY[key]
        return _call_resolver(resolver)

    pyta2_cls = _resolve_from_pyta2_top_level(key)
    if pyta2_cls is not None:
        return pyta2_cls

    pyta2_cls = _resolve_from_pyta2_ma_api(key)
    if pyta2_cls is not None:
        return pyta2_cls

    raise ValueError(f"unknown pyta2 indicator: {indicator!r}")


def resolve_pyta2_default_inputs(indicator: str | type) -> tuple[str, ...] | None:
    if not isinstance(indicator, str):
        return None

    key = _normalize_indicator_name(indicator)
    if key in _PYTA2_REGISTRY:
        _, default_inputs = _PYTA2_REGISTRY[key]
        return default_inputs
    return None


def normalize_pyta2_inputs(inputs: Sequence[str]) -> tuple[str, ...]:
    normalized = []
    for item in inputs:
        key = item.strip().lower()
        try:
            normalized.append(_FIELD_ALIASES[key])
        except KeyError as exc:
            raise ValueError(
                f"unknown kline input field {item!r}; expected one of "
                f"{sorted(_FIELD_ALIASES)}"
            ) from exc
    return tuple(normalized)


def _normalize_indicator_name(name: str) -> str:
    key = name.strip()
    if key.startswith("r") and len(key) > 1 and key[1].isupper():
        key = key[1:]
    return key.upper()


def _call_resolver(resolver: IndicatorResolver) -> type:
    if isinstance(resolver, type):
        return resolver
    return resolver()


def _resolve_from_pyta2_top_level(key: str) -> type | None:
    import pyta2

    for attr in (key, f"r{key}"):
        candidate = getattr(pyta2, attr, None)
        if isinstance(candidate, type):
            return candidate
    return None


def _resolve_from_pyta2_ma_api(key: str) -> type | None:
    try:
        from pyta2.trend.ma.api import get_ma_class

        return get_ma_class(key)
    except (ImportError, ValueError):
        return None


def _resolve_sma_class() -> type:
    from pyta2.trend.ma.api import get_ma_class

    return get_ma_class("SMA")


register_pyta2_indicator("SMA", _resolve_sma_class, default_inputs=("close",))
