from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pyta2.base.utils import get_outputs
from pyta2.utils.vector import VectorTable

from .signal import rSignal


def forward_step_apply(
    data: Iterable[Mapping[str, Any]],
    signal: rSignal,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """从 Signal 当前状态逐条重放，并按逻辑观测整理标量输出。"""
    if not isinstance(signal, rSignal):
        raise TypeError("signal 必须是 rSignal 实例")

    schema = signal.schema.get_dtypes() if signal.schema is not None else None
    outputs = VectorTable(schema=schema)
    for inputs in data:
        previous_index = signal.g_index
        result = signal.step(**inputs)

        # 未声明 schema 时不能根据首个结果推断数值类型。
        if schema is None and len(outputs) == 0:
            for name in result:
                outputs.ensure_column(name, dtype=object)

        # 同一未结束观测的更新替换原结果。
        if len(outputs) and signal.g_index == previous_index:
            outputs.update_row(-1, result)
        else:
            outputs.append(result)

    result = get_outputs(outputs, return_type=return_type)
    if return_meta_info:
        return result, signal.meta_info
    return result


__all__ = ["forward_step_apply"]
