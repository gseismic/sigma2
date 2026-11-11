"""查询 step 的调用签名及显式声明的输入值结构。"""

from __future__ import annotations

import inspect
from numbers import Number
from typing import Any


def _error(cls: type, parameter: str, path: str, message: str, *, kind=ValueError):
    raise kind(
        f"{cls.__module__}.{cls.__qualname__} 参数 {parameter!r}{path}: {message}"
    )


def _clone_node(
    node: Any, cls: type, parameter: str, path: str, active: set[int]
) -> dict[str, Any]:
    if not isinstance(node, dict):
        _error(cls, parameter, path, "节点必须是字典", kind=TypeError)
    if id(node) in active:
        _error(cls, parameter, path, "描述不能包含循环引用")
    active.add(id(node))
    try:
        node_type = node.get("type")
        if not isinstance(node_type, str):
            _error(
                cls, parameter, path + ".type", "必须是类型名称字符串", kind=TypeError
            )
        properties = {
            "unknown": set(),
            "number": {"enum"},
            "boolean": {"enum"},
            "string": {"enum"},
            "mapping": {"keys", "values"},
            "object": {"fields", "allow_extra"},
            "sequence": {"items"},
            "tuple": {"items"},
        }
        if node_type not in properties:
            _error(cls, parameter, path + ".type", f"不支持的类型 {node_type!r}")
        extra = node.keys() - ({"type", "nullable"} | properties[node_type])
        if extra:
            _error(cls, parameter, path, f"不支持的键 {tuple(map(repr, extra))}")

        result: dict[str, Any] = {"type": node_type}
        if "nullable" in node:
            if type(node["nullable"]) is not bool:
                _error(
                    cls, parameter, path + ".nullable", "必须是布尔值", kind=TypeError
                )
            result["nullable"] = node["nullable"]

        if "enum" in node:
            values = node["enum"]
            if not isinstance(values, list):
                _error(cls, parameter, path + ".enum", "必须是列表", kind=TypeError)
            if not values:
                _error(cls, parameter, path + ".enum", "列表不能为空")
            for index, value in enumerate(values):
                valid = (
                    (
                        node_type == "number"
                        and isinstance(value, Number)
                        and not isinstance(value, bool)
                    )
                    or (node_type == "boolean" and type(value) is bool)
                    or (node_type == "string" and isinstance(value, str))
                )
                if not valid:
                    _error(
                        cls,
                        parameter,
                        f"{path}.enum[{index}]",
                        "值与节点类型不符或为 None",
                        kind=TypeError,
                    )
            result["enum"] = list(values)

        if node_type == "mapping":
            for key in ("keys", "values"):
                if key not in node:
                    _error(cls, parameter, path, f"缺少 {key!r}")
                result[key] = _clone_node(
                    node[key], cls, parameter, path + "." + key, active
                )
        elif node_type == "object":
            fields = node.get("fields")
            if not isinstance(fields, dict):
                _error(
                    cls, parameter, path + ".fields", "必须是字段字典", kind=TypeError
                )
            if id(fields) in active:
                _error(cls, parameter, path + ".fields", "描述不能包含循环引用")
            if type(node.get("allow_extra")) is not bool:
                _error(
                    cls,
                    parameter,
                    path + ".allow_extra",
                    "必须显式声明布尔值",
                    kind=TypeError,
                )
            active.add(id(fields))
            try:
                copied_fields = {}
                for name, field in fields.items():
                    field_path = f"{path}.fields[{name!r}]"
                    if not isinstance(name, str):
                        _error(
                            cls,
                            parameter,
                            field_path,
                            "字段名必须是字符串",
                            kind=TypeError,
                        )
                    if not isinstance(field, dict):
                        _error(
                            cls,
                            parameter,
                            field_path,
                            "字段声明必须是字典",
                            kind=TypeError,
                        )
                    if id(field) in active:
                        _error(cls, parameter, field_path, "描述不能包含循环引用")
                    if field.keys() != {"required", "schema"}:
                        _error(
                            cls,
                            parameter,
                            field_path,
                            "字段必须且只能包含 required 和 schema",
                        )
                    if type(field["required"]) is not bool:
                        _error(
                            cls,
                            parameter,
                            field_path + ".required",
                            "必须是布尔值",
                            kind=TypeError,
                        )
                    active.add(id(field))
                    try:
                        copied_fields[name] = {
                            "required": field["required"],
                            "schema": _clone_node(
                                field["schema"],
                                cls,
                                parameter,
                                field_path + ".schema",
                                active,
                            ),
                        }
                    finally:
                        active.remove(id(field))
            finally:
                active.remove(id(fields))
            result["fields"] = copied_fields
            result["allow_extra"] = node["allow_extra"]
        elif node_type == "sequence":
            if "items" not in node:
                _error(cls, parameter, path, "缺少 'items'")
            result["items"] = _clone_node(
                node["items"], cls, parameter, path + ".items", active
            )
        elif node_type == "tuple":
            items = node.get("items")
            if not isinstance(items, list):
                _error(
                    cls, parameter, path + ".items", "必须是节点列表", kind=TypeError
                )
            if id(items) in active:
                _error(cls, parameter, path + ".items", "描述不能包含循环引用")
            active.add(id(items))
            try:
                result["items"] = [
                    _clone_node(item, cls, parameter, f"{path}.items[{index}]", active)
                    for index, item in enumerate(items)
                ]
            finally:
                active.remove(id(items))
        return result
    finally:
        active.remove(id(node))


def describe_input(cls: type) -> dict[str, Any]:
    """按实际 step 签名和普通类属性声明构造独立的查询结果。"""
    step = cls.step
    parameters = list(inspect.signature(step).parameters.values())
    # 普通实例方法的首个位置参数是接收者；类方法已绑定，静态方法无接收者。
    descriptor = inspect.getattr_static(cls, "step")
    if not isinstance(descriptor, (staticmethod, classmethod)) and parameters:
        if parameters[0].kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            parameters.pop(0)

    details = getattr(cls, "input_schema_details", {})
    if not isinstance(details, dict):
        raise TypeError(
            f"{cls.__module__}.{cls.__qualname__}.input_schema_details 必须是字典"
        )
    names = {parameter.name for parameter in parameters}
    for name in details:
        if name not in names:
            _error(cls, str(name), "", "声明参数不存在于 step 签名")

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
        entry["schema"] = _clone_node(
            details.get(parameter.name, {"type": "unknown"}),
            cls,
            parameter.name,
            "",
            set(),
        )
        result[parameter.name] = entry
    return {"parameters": result}
