from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Callable

from pyta2.base.schema import Schema
from pyta2.utils.space import Space
from sigma2.core import rKlineWindowSignal
from sigma2.utils.pyta2 import normalize_pyta2_inputs


class rKlineEffectSignal(rKlineWindowSignal):
    """把 stateless pyta2 effect 绑定到标准 K 线输入。"""

    name = "kline_effect"

    def __init__(
        self,
        effect_cls: type,
        *,
        effect_args: Sequence[Any] = (),
        effect_kwargs: dict[str, Any] | None = None,
        inputs: Sequence[str],
        schema: list[tuple[str, Space]] | dict[str, Space] | Schema | None = None,
        output_transform: Callable[[Any], Any] | None = None,
        full_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.effect_cls = effect_cls
        self.effect_args = tuple(effect_args)
        self.effect_kwargs = dict(effect_kwargs or {})
        self.inputs = normalize_pyta2_inputs(inputs)
        self.output_transform = output_transform
        self._full_name = full_name
        effect = self._make_effect()
        super().__init__(
            window=effect.window,
            schema=effect.schema if schema is None else schema,
            extra_window=effect.extra_window,
            **kwargs,
        )

    def reset_window_extras(self) -> None:
        pass

    def forward(self, opens, highs, lows, closes, volumes) -> Any:
        effect = self._make_effect()
        output = effect.backward(*self._effect_args_from_arrays(opens, highs, lows, closes, volumes))
        if self.output_transform is not None:
            return self.output_transform(output)
        return output

    @property
    def full_name(self) -> str:
        if self._full_name is not None:
            return self._full_name
        return f"{self.name}[{','.join(self.inputs)}]"

    def _make_effect(self):
        kwargs = dict(self.effect_kwargs)
        kwargs.setdefault("buffer_size", 1)
        kwargs["return_dict"] = False
        return self.effect_cls(*self.effect_args, **kwargs)

    def _effect_args_from_arrays(self, opens, highs, lows, closes, volumes) -> tuple[Any, ...]:
        arrays = {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }
        return tuple(arrays[field] for field in self.inputs)
