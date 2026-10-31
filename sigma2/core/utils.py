from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pyta2.base.utils import get_outputs
from pyta2.utils.vector import VectorTable

from .operator import _storage_dtypes, rOperator


def forward_step_apply(
    data: Iterable[Mapping[str, Any]],
    operator: rOperator,
    *,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """从当前状态重放，按结果所属的逻辑观测整理输出。"""
    if not isinstance(operator, rOperator):
        raise TypeError("operator 必须是 rOperator 实例")

    schema = None
    missing = None
    if operator.schema is not None:
        schema = _storage_dtypes(operator.schema)
        missing = {key: space.null_value for key, space in operator.schema.items()}
    outputs = VectorTable(schema=schema)
    # 在消费输入和推进算子前检查输出格式及所需依赖。
    get_outputs(outputs, return_type=return_type)
    first_index = None
    for inputs in data:
        previous_index = operator.g_index
        result = operator.step(**inputs)

        # 未声明 schema 时不能根据首个结果推断数值类型。
        if schema is None and len(outputs) == 0:
            for name in result:
                outputs.ensure_column(name, dtype=object)
            missing = dict.fromkeys(result)

        if first_index is None:
            first_index = operator.g_index
        if len(outputs) == 0 or operator.g_index != previous_index:
            outputs.append(missing)

        # Outcome 的结果属于历史锚点；之前的锚点不属于本次返回范围。
        row = operator.result_index - first_index
        if 0 <= row < len(outputs):
            outputs.update_row(row, result)

    result = get_outputs(outputs, return_type=return_type)
    if return_meta_info:
        return result, operator.meta_info
    return result


__all__ = ["forward_step_apply"]
