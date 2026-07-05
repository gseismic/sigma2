from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from sigma2._pyta2 import ensure_pyta2_importable
from sigma2.families import rKlineWindowSignal

ensure_pyta2_importable()

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


def register_pyta2_indicator(
    name: str,
    indicator: IndicatorResolver,
    *,
    default_inputs: Sequence[str] = ("close",),
) -> None:
    """注册 pyta2 rolling indicator 名称映射。"""

    key = _normalize_indicator_name(name)
    _PYTA2_REGISTRY[key] = (indicator, _normalize_inputs(default_inputs))


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


def pyta2_signal(
    indicator: str | type,
    *,
    params: dict[str, Any] | None = None,
    field: str | None = None,
    inputs: Sequence[str] | None = None,
    **kwargs: Any,
) -> "rPyta2Signal":
    """用名称或 class 快捷构造 pyta2 适配信号。"""

    return rPyta2Signal(
        indicator,
        params=params,
        field=field,
        inputs=inputs,
        **kwargs,
    )


class rPyta2Signal(rKlineWindowSignal):
    """把 pyta2 rolling indicator 适配成标准 K 线 step signal。"""

    family = "kline"

    def __init__(
        self,
        indicator: str | type,
        *,
        params: dict[str, Any] | None = None,
        field: str | None = None,
        inputs: Sequence[str] | None = None,
        full_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        if field is not None and inputs is not None:
            raise ValueError("field and inputs cannot both be provided")

        self.indicator_name = indicator if isinstance(indicator, str) else indicator.__name__
        self.indicator_cls = resolve_pyta2_indicator(indicator)
        self.indicator_params = dict(params or {})
        self.inputs = self._resolve_inputs(indicator, field=field, inputs=inputs)
        self._full_name = full_name
        self._indicator = self._make_indicator()

        super().__init__(
            window=self._indicator.window,
            schema=self._indicator.schema,
            extra_window=self._indicator.extra_window,
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        self._indicator = self._make_indicator()

    def _step_forward(
        self,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ) -> Any:
        self._window.append(
            {
                "open": open,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
        return self._indicator.rolling(*self._indicator_args_from_window())

    def forward(self, opens, highs, lows, closes, volumes) -> Any:
        temp_indicator = self._make_indicator()
        values = self._indicator_args_from_arrays(opens, highs, lows, closes, volumes)
        return temp_indicator.rolling(*values)

    @property
    def full_name(self) -> str:
        if self._full_name is not None:
            return self._full_name
        return f"{self._indicator.full_name}[{','.join(self.inputs)}]"

    def _make_indicator(self):
        params = dict(self.indicator_params)
        params.setdefault("buffer_size", 1)
        params["return_dict"] = False
        return self.indicator_cls(**params)

    def _indicator_args_from_window(self) -> tuple[Any, ...]:
        arrays = {
            "open": self._window["open"],
            "high": self._window["high"],
            "low": self._window["low"],
            "close": self._window["close"],
            "volume": self._window["volume"],
        }
        return tuple(arrays[field] for field in self.inputs)

    def _indicator_args_from_arrays(
        self,
        opens,
        highs,
        lows,
        closes,
        volumes,
    ) -> tuple[Any, ...]:
        arrays = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }
        return tuple(arrays[field] for field in self.inputs)

    def _resolve_inputs(
        self,
        indicator: str | type,
        *,
        field: str | None,
        inputs: Sequence[str] | None,
    ) -> tuple[str, ...]:
        if field is not None:
            return _normalize_inputs((field,))
        if inputs is not None:
            return _normalize_inputs(inputs)
        if isinstance(indicator, str):
            key = _normalize_indicator_name(indicator)
            if key in _PYTA2_REGISTRY:
                _, default_inputs = _PYTA2_REGISTRY[key]
                return default_inputs
        return ("close",)


class rPyta2SMA(rPyta2Signal):
    """pyta2 rSMA 的类式快捷适配。"""

    name = "pyta2_sma"

    def __init__(self, n: int, *, field: str = "close", **kwargs: Any) -> None:
        if n <= 0:
            raise ValueError(f"n must be greater than 0, got {n}")
        self.n = n
        self.field = field
        super().__init__(
            "SMA",
            params={"n": n},
            field=field,
            **kwargs,
        )


def _normalize_indicator_name(name: str) -> str:
    key = name.strip()
    if key.startswith("r") and len(key) > 1 and key[1].isupper():
        key = key[1:]
    return key.upper()


def _normalize_inputs(inputs: Sequence[str]) -> tuple[str, ...]:
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
