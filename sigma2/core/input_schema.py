"""查询 step 的调用签名及显式声明的输入描述。"""

from __future__ import annotations

import inspect
from copy import deepcopy
from typing import Any


def describe_input(cls: type) -> dict[str, Any]:
    """按实际 step 签名和普通字典列表构造查询结果。"""
    parameters = list(inspect.signature(cls.step).parameters.values())
    # 普通实例方法的首个位置参数是接收者；类方法已绑定，静态方法无接收者。
    descriptor = inspect.getattr_static(cls, "step")
    if not isinstance(descriptor, (staticmethod, classmethod)) and parameters:
        if parameters[0].kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            parameters.pop(0)

    label = f"{cls.__module__}.{cls.__qualname__}.input_schema_details"
    declarations = cls.input_schema_details
    if not isinstance(declarations, list):
        raise TypeError(f"{label} 必须是列表")

    names = {parameter.name for parameter in parameters}
    details = {}
    for index, declaration in enumerate(declarations):
        if not isinstance(declaration, dict) or not isinstance(
            declaration.get("name"), str
        ):
            raise TypeError(f"{label}[{index}] 必须是包含字符串 name 的字典")
        name = declaration["name"]
        if name not in names:
            raise ValueError(f"{label} 参数 {name!r} 不存在于 step 签名")
        if name in details:
            raise ValueError(f"{label} 参数 {name!r} 重复声明")
        reserved = declaration.keys() & {"kind", "required", "default"}
        if reserved:
            raise ValueError(f"{label} 参数 {name!r} 的 {sorted(reserved)} 由签名决定")
        details[name] = declaration

    result = {}
    for parameter in parameters:
        variadic = parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        )
        entry = {
            "kind": parameter.kind.name.lower(),
            "required": not variadic and parameter.default is inspect.Parameter.empty,
        }
        if parameter.default is not inspect.Parameter.empty:
            entry["default"] = parameter.default
        schema = deepcopy(
            {
                key: value
                for key, value in details.get(parameter.name, {}).items()
                if key != "name"
            }
        )
        schema.setdefault("type", "unknown")
        entry["schema"] = schema
        result[parameter.name] = entry
    return {"parameters": result}
