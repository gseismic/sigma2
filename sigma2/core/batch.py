from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from itertools import chain
from typing import Any

import numpy as np

from sigma2.kline.data import KlineBar
from sigma2.kline_bundle.data import KlineBundle
from .kline import _KlineInput
from .kline_bundle import _KlineBundleInput
from .signal import rOperator, rOutcome, rSignal


def forward_signal_apply(
    data: Any,
    signal_cls: type[rSignal],
    param_args: Sequence[Any] | None = None,
    param_kwargs: Mapping[str, Any] | None = None,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbols: Sequence[str] | None = None,
    symbol: str | None = None,
) -> Any:
    """重放 Signal；K 线和截面分别接收 Bar 与 Bundle 序列。"""
    if not isinstance(signal_cls, type) or not issubclass(signal_cls, rSignal):
        raise TypeError("signal_cls must be an rSignal subclass")
    return _forward_apply(
        data,
        signal_cls,
        param_args,
        param_kwargs,
        return_type,
        return_meta_info,
        symbols,
        symbol,
    )


def forward_outcome_apply(
    data: Any,
    outcome_cls: type[rOutcome],
    param_args: Sequence[Any] | None = None,
    param_kwargs: Mapping[str, Any] | None = None,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
    symbols: Sequence[str] | None = None,
    symbol: str | None = None,
) -> Any:
    """重放 Outcome，并将成熟结果回填到所属锚点。"""
    if not isinstance(outcome_cls, type) or not issubclass(outcome_cls, rOutcome):
        raise TypeError("outcome_cls must be an rOutcome subclass")
    return _forward_apply(
        data,
        outcome_cls,
        param_args,
        param_kwargs,
        return_type,
        return_meta_info,
        symbols,
        symbol,
    )


def _forward_apply(
    data: Any,
    operator_cls: type[rOperator],
    param_args: Sequence[Any] | None,
    param_kwargs: Mapping[str, Any] | None,
    return_type: str,
    return_meta_info: bool,
    symbols: Sequence[str] | None,
    symbol: str | None,
) -> Any:
    normalized = _normalize_return_type(return_type)
    if not isinstance(return_meta_info, bool):
        raise TypeError("return_meta_info must be bool")
    args = () if param_args is None else tuple(param_args)
    kwargs = {} if param_kwargs is None else dict(param_kwargs)
    if "return_dict" in kwargs and kwargs["return_dict"] is not True:
        raise ValueError("batch replay requires return_dict=True")
    kwargs["return_dict"] = True
    kwargs.setdefault("buffer_size", 0)

    is_bundle = issubclass(operator_cls, _KlineBundleInput)
    is_single = issubclass(operator_cls, _KlineInput)
    is_kline = is_bundle or is_single
    if is_kline:
        if symbols is not None and not is_bundle:
            raise ValueError("symbols is only supported for KlineBundle operators")
        if symbol is not None and not is_single:
            raise ValueError("symbol is only supported for single K-line operators")
        if is_bundle and symbols is not None:
            if "symbols" in kwargs and tuple(kwargs["symbols"]) != tuple(symbols):
                raise ValueError("symbols conflicts with param_kwargs['symbols']")
            kwargs["symbols"] = symbols
        if is_single and symbol is not None:
            if "symbol" in kwargs and kwargs["symbol"] != symbol:
                raise ValueError("symbol conflicts with param_kwargs['symbol']")
            kwargs["symbol"] = symbol
        events = iter(data)
        sentinel = object()
        first = next(events, sentinel)
        expected_type = KlineBundle if is_bundle else KlineBar
        if first is not sentinel and not isinstance(first, expected_type):
            raise TypeError(
                f"K-line batch data must contain {expected_type.__name__} objects"
            )
        if is_bundle and "symbols" not in kwargs:
            kwargs["symbols"] = () if first is sentinel else first.symbols
        events = events if first is sentinel else chain((first,), events)
    else:
        if symbols is not None or symbol is not None:
            raise ValueError(
                "symbol and symbols are only supported for K-line operators"
            )
        events = _column_events(data, operator_cls.step_input_keys)

    operator = operator_cls(*args, **kwargs)
    rows: dict[str, list[Any]] = {key: [] for key in operator.output_keys}
    times: list[Any] = []
    input_available: list[Any] = []
    result_input_ready: list[Any] = []
    emission_bar_times: list[Any] = []
    all_known = True
    latest_available = None
    is_outcome = isinstance(operator, rOutcome)

    for event in events:
        missing = (
            operator.missing_symbols()
            if is_bundle and operator.per_symbol
            else operator.missing_output
        )
        missing_row = operator.make_dict_output(missing)
        for key in operator.output_keys:
            rows[key].append(deepcopy(missing_row[key]))
        result_input_ready.append(None)
        emission_bar_times.append(None)

        if is_kline:
            output = operator.step(event)
            times.append(event.bar_time)
            input_available.append(event.available_at)
            if event.available_at is None:
                all_known = False
            elif latest_available is None or event.available_at > latest_available:
                latest_available = event.available_at
        else:
            output = operator.step(**event)
        target = operator.result_index if is_outcome else operator.g_index
        if target >= 0:
            for key in operator.output_keys:
                rows[key][target] = deepcopy(output[key])
            if is_kline:
                emission_bar_times[target] = event.bar_time
                if all_known:
                    result_input_ready[target] = latest_available

    columns: dict[str, np.ndarray] = {}
    for key, factor_name in zip(operator.output_keys, operator.factor_names):
        space = operator.schema[key]
        if rows[key]:
            columns[factor_name] = np.asarray(rows[key], dtype=space.dtype)
        else:
            symbol_axis = (
                (len(operator.symbols),) if is_bundle and operator.per_symbol else ()
            )
            shape = (0, *symbol_axis, *tuple(getattr(space, "shape", ())))
            columns[factor_name] = np.empty(shape, dtype=space.dtype)

    result = _format_result(
        columns,
        normalized,
        times=times if is_kline else None,
        symbols=operator.symbols if is_bundle and operator.per_symbol else None,
    )
    if return_meta_info:
        metadata = operator.meta_info
        if is_kline:
            metadata.update(
                {
                    "bar_times": tuple(times),
                    "input_available_at": tuple(input_available),
                    "emission_bar_times": tuple(emission_bar_times),
                    # 包含此前全部输入；计算和发布延迟由消费方另行提供。
                    "result_input_ready_at": tuple(result_input_ready),
                }
            )
        return result, metadata
    return result


def _column_events(data: Any, required_keys: Sequence[str]) -> Iterable[dict[str, Any]]:
    keys_method = getattr(data, "keys", None)
    if not callable(keys_method) or not hasattr(data, "__getitem__"):
        raise TypeError("data must provide keys() and __getitem__()")
    missing = [key for key in required_keys if key not in set(keys_method())]
    if missing:
        raise KeyError(f"data is missing required columns: {missing}")
    columns = {}
    expected_length = None
    for key in required_keys:
        column = data[key]
        to_numpy = getattr(column, "to_numpy", None)
        values = np.asarray(to_numpy() if callable(to_numpy) else column)
        if values.ndim != 1:
            raise ValueError(
                f"data column {key!r} must be one-dimensional, got {values.shape}"
            )
        if expected_length is None:
            expected_length = len(values)
        elif len(values) != expected_length:
            raise ValueError("all required data columns must have the same length")
        columns[key] = values
    length = 0 if expected_length is None else expected_length
    for index in range(length):
        yield {key: values[index] for key, values in columns.items()}


def _format_result(
    columns: dict[str, np.ndarray],
    return_type: str,
    *,
    times: list[Any] | None,
    symbols: tuple[str, ...] | None,
) -> Any:
    if return_type == "dict":
        return columns
    if return_type == "tuple":
        values = tuple(columns.values())
        return values[0] if len(values) == 1 else values
    if return_type == "list":
        length = len(next(iter(columns.values()))) if columns else 0
        return [
            {key: values[index] for key, values in columns.items()}
            for index in range(length)
        ]
    if return_type in {"dataframe", "pd.dataframe"}:
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError("return_type='dataframe' requires pandas") from exc
        if times is None:
            return pd.DataFrame(columns)
        if symbols is None:
            return pd.DataFrame(columns, index=pd.Index(times, name="bar_time"))
        index = pd.MultiIndex.from_product(
            [times, symbols], names=["bar_time", "symbol"]
        )
        data = {
            key: values.reshape(-1)
            if values.ndim == 2
            else list(values.reshape(len(index), *values.shape[2:]))
            for key, values in columns.items()
        }
        return pd.DataFrame(data, index=index)
    if return_type == "pl.dataframe":
        try:
            import polars as pl
        except ImportError as exc:
            raise ImportError("return_type='pl.dataframe' requires polars") from exc
        if times is None:
            return pl.DataFrame(columns)
        if symbols is None:
            return pl.DataFrame(
                {"bar_time": times, **{k: v.tolist() for k, v in columns.items()}}
            )
        data = {
            "bar_time": [time for time in times for _ in symbols],
            "symbol": [symbol for _ in times for symbol in symbols],
        }
        data.update(
            {
                key: values.reshape(
                    len(times) * len(symbols), *values.shape[2:]
                ).tolist()
                for key, values in columns.items()
            }
        )
        return pl.DataFrame(data)
    raise RuntimeError(f"unreachable return type: {return_type!r}")


def _normalize_return_type(return_type: str) -> str:
    if not isinstance(return_type, str):
        raise TypeError("return_type must be str")
    value = return_type.strip().lower()
    if value not in {
        "dict",
        "tuple",
        "list",
        "dataframe",
        "pd.dataframe",
        "pl.dataframe",
    }:
        raise ValueError(f"unsupported return_type: {return_type!r}")
    return value


__all__ = ["forward_signal_apply", "forward_outcome_apply"]
