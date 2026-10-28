from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

import numpy as np

from sigma2.core import (
    KlineBar,
    rKlineBundleOutcome,
    rKlineBundleSignal,
    rKlineOutcome,
    rKlineSignal,
)


class _BundleMap:
    """把单 K 线算子按 symbol 隔离，并逐共同快照推进所有子算子。"""

    _component_base: type

    def __init__(
        self,
        operator_cls: type,
        *operator_args: Any,
        symbols: Sequence[str],
        operator_kwargs: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if not isinstance(operator_cls, type) or not issubclass(
            operator_cls, self._component_base
        ):
            raise TypeError(
                f"operator_cls must derive from {self._component_base.__name__}"
            )
        params = dict(operator_kwargs or {})
        reserved = {"symbol", "buffer_size", "return_dict"} & params.keys()
        if reserved:
            raise ValueError(f"operator_kwargs cannot contain {sorted(reserved)}")
        self._prototype = operator_cls(
            *operator_args, **params, buffer_size=0, return_dict=True
        )
        timing = {"n_backward": self._prototype.n_backward}
        if isinstance(self._prototype, rKlineOutcome):
            timing["n_forward"] = self._prototype.n_forward
        if "per_symbol" in kwargs and kwargs["per_symbol"] is not True:
            raise ValueError(
                "mapping a single-symbol operator requires per_symbol=True"
            )
        super().__init__(self._prototype.schema, symbols=symbols, **timing, **kwargs)

    def reset_extras(self) -> None:
        self._operators = [deepcopy(self._prototype) for _ in self.symbols]
        for operator in self._operators:
            operator.reset()

    def forward(self, bundle):
        values: dict[str, list[Any]] = {key: [] for key in self.output_keys}
        for symbol, operator in zip(self.symbols, self._operators):
            bar = bundle.get(symbol)
            if bar is None:
                bar = KlineBar(
                    symbol=symbol,
                    bar_time=bundle.bar_time,
                    open=np.nan,
                    high=np.nan,
                    low=np.nan,
                    close=np.nan,
                    volume=np.nan,
                    available_at=bundle.available_at,
                    is_missing=True,
                )
            result = operator.step(bar)
            for key in self.output_keys:
                values[key].append(result[key])
        columns = []
        for key in self.output_keys:
            if values[key]:
                columns.append(np.asarray(values[key]))
            else:
                shape = (0, *tuple(getattr(self.schema[key], "shape", ())))
                columns.append(np.empty(shape, dtype=self.schema[key].dtype))
        return columns[0] if len(columns) == 1 else tuple(columns)

    @property
    def full_name(self) -> str:
        return self._prototype.full_name

    @property
    def meta_info(self) -> dict[str, Any]:
        info = super().meta_info
        info["component"] = self._prototype.meta_info
        return info


class rKlineBundleMapSignal(_BundleMap, rKlineBundleSignal):
    """将单 K 线 Signal 复用到一个截面的全部 symbol。"""

    _component_base = rKlineSignal


class rKlineBundleMapOutcome(_BundleMap, rKlineBundleOutcome):
    """将单 K 线 Outcome 复用到共同快照时间轴。"""

    _component_base = rKlineOutcome


__all__ = ["rKlineBundleMapSignal", "rKlineBundleMapOutcome"]
