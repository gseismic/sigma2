from __future__ import annotations


def qualify_factor_name(scope: str | None, formula_name: str) -> str:
    """由独立保存的作用域和公式名生成展示或训练使用的名称。"""
    if scope is not None and (not isinstance(scope, str) or not scope):
        raise ValueError("scope must be a non-empty string or None")
    if not isinstance(formula_name, str) or not formula_name:
        raise ValueError("formula_name must be a non-empty string")
    return formula_name if scope is None else f"{scope}:{formula_name}"


__all__ = ["qualify_factor_name"]
