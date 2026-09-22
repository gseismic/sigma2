from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .signal import rSignal


def forward_signal_apply(
    data: Any,
    signal_cls: type[rSignal],
    param_args: Sequence[Any] | None = None,
    param_kwargs: Mapping[str, Any] | None = None,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """把列式 family 数据逐行 replay 到一个新的 Signal 实例。

    ``data`` 只需提供 ``keys()`` 和 ``__getitem__()``；实际必需列由
    ``signal_cls.step_input_keys`` 决定。该函数只调用公共 ``step()``，从而让
    batch 与在线 finalized replay 共用同一套状态和计算逻辑。
    """

    if not isinstance(signal_cls, type) or not issubclass(signal_cls, rSignal):
        raise TypeError("signal_cls must be an rSignal subclass")
    normalized_return_type = _normalize_return_type(return_type)
    if not isinstance(return_meta_info, bool):
        raise TypeError(
            "return_meta_info must be bool, "
            f"got {type(return_meta_info).__name__}"
        )

    args = () if param_args is None else tuple(param_args)
    kwargs = {} if param_kwargs is None else dict(param_kwargs)
    if "return_dict" in kwargs and kwargs["return_dict"] is not True:
        raise ValueError("forward_signal_apply requires return_dict=True")
    kwargs["return_dict"] = True
    kwargs.setdefault("buffer_size", 1)
    signal = signal_cls(*args, **kwargs)

    columns, length = _normalize_columns(data, signal.step_input_keys)
    output_values: dict[str, list[Any]] = {
        key: [] for key in signal.output_keys
    }
    for index in range(length):
        event = {key: values[index] for key, values in columns.items()}
        row = signal.step(**event)
        for key in signal.output_keys:
            output_values[key].append(row[key])

    factor_columns = {
        factor_name: np.asarray(
            output_values[output_key],
            dtype=signal.schema[output_key].dtype,
        )
        for output_key, factor_name in zip(
            signal.output_keys,
            signal.factor_names,
        )
    }
    result = _format_result(factor_columns, normalized_return_type)
    if return_meta_info:
        return result, signal.meta_info
    return result


def _normalize_columns(
    data: Any,
    required_keys: Sequence[str],
) -> tuple[dict[str, NDArray[Any]], int]:
    keys_method = getattr(data, "keys", None)
    if not callable(keys_method) or not hasattr(data, "__getitem__"):
        raise TypeError(
            "data must be a columnar object providing keys() and __getitem__()"
        )

    available_keys = set(keys_method())
    missing = [key for key in required_keys if key not in available_keys]
    if missing:
        raise KeyError(f"data is missing required columns: {missing}")

    columns: dict[str, NDArray[Any]] = {}
    expected_length: int | None = None
    for key in required_keys:
        column = data[key]
        to_numpy = getattr(column, "to_numpy", None)
        if callable(to_numpy):
            column = to_numpy()
        values = np.asarray(column)
        if values.ndim != 1:
            raise ValueError(
                f"data column {key!r} must be one-dimensional, got shape {values.shape}"
            )
        if expected_length is None:
            expected_length = len(values)
        elif len(values) != expected_length:
            raise ValueError(
                "all required data columns must have the same length; "
                f"column {key!r} has length {len(values)}, expected {expected_length}"
            )
        columns[key] = values

    return columns, 0 if expected_length is None else expected_length


def _format_result(
    factor_columns: dict[str, NDArray[Any]],
    return_type: str,
) -> Any:
    if return_type == "dict":
        return factor_columns
    if return_type == "tuple":
        values = tuple(factor_columns.values())
        return values[0] if len(values) == 1 else values
    if return_type == "list":
        if not factor_columns:
            return []
        names = tuple(factor_columns)
        length = len(next(iter(factor_columns.values())))
        return [
            {name: factor_columns[name][index] for name in names}
            for index in range(length)
        ]
    if return_type in {"dataframe", "pd.dataframe"}:
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "return_type='dataframe' requires pandas to be installed"
            ) from exc
        return pd.DataFrame(factor_columns)
    if return_type == "pl.dataframe":
        try:
            import polars as pl
        except ImportError as exc:
            raise ImportError(
                "return_type='pl.dataframe' requires polars to be installed"
            ) from exc
        return pl.DataFrame(factor_columns)

    raise RuntimeError(f"unreachable normalized return_type: {return_type!r}")


def _normalize_return_type(return_type: str) -> str:
    if not isinstance(return_type, str):
        raise TypeError(
            f"return_type must be str, got {type(return_type).__name__}"
        )
    normalized = return_type.strip().lower()
    supported = {
        "dict",
        "tuple",
        "list",
        "dataframe",
        "pd.dataframe",
        "pl.dataframe",
    }
    if normalized not in supported:
        raise ValueError(
            "return_type must be one of 'dict', 'tuple', 'list', 'dataframe', "
            "'pd.dataframe' or 'pl.dataframe', "
            f"got {return_type!r}"
        )
    return normalized


__all__ = ["forward_signal_apply"]
