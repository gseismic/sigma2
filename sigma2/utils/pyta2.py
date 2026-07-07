from __future__ import annotations

import importlib
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

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


def ensure_pyta2_importable() -> None:
    """确保安装包布局和本地软链接布局都能导入 pyta2。"""

    if _can_import_pyta2():
        return

    _clear_pyta2_modules()
    package_root = Path(__file__).resolve().parents[2]
    candidates = (
        package_root / "pyta2",
        package_root.parent / "pyta2",
    )
    for candidate in candidates:
        if _looks_like_pyta2_repo(candidate):
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
            importlib.invalidate_caches()
            _clear_pyta2_modules()
            if _can_import_pyta2():
                return

    raise ModuleNotFoundError(
        "sigma2 requires pyta2. Install pyta2 or expose the local pyta2 repo "
        "on PYTHONPATH."
    )


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


def _can_import_pyta2() -> bool:
    try:
        importlib.import_module("pyta2.base.schema")
        importlib.import_module("pyta2.utils.deque")
    except ModuleNotFoundError:
        return False
    return True


def _clear_pyta2_modules() -> None:
    for name in list(sys.modules):
        if name == "pyta2" or name.startswith("pyta2."):
            del sys.modules[name]


def _looks_like_pyta2_repo(path: Path) -> bool:
    return (path / "pyta2" / "base" / "schema.py").is_file()


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
