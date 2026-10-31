from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from pyta2.base.schema import Schema
from pyta2.utils.deque import DequeTable
from pyta2.utils.validation import ensure_integer


def _storage_dtypes(schema: Schema) -> dict[str, Any]:
    """为多维输出和可空输出保留对象列。"""
    return {
        key: (
            space.dtype
            if space.null_value is not None and getattr(space, "shape", ()) == ()
            else object
        )
        for key, space in schema.items()
    }


class rOperator(ABC):
    """逐条推进有状态算子，统一管理索引、输出缓存和失败锁定。"""

    name: str | None = None
    family: str | None = None
    full_name: str | None = None

    def __init__(
        self,
        *,
        schema: Mapping[str, Any] | None = None,
        n_backward: int = 0,
        n_forward: int = 0,
        buffer_size: int = 1,
        used_fields: tuple[str, ...] | None = None,
    ) -> None:
        self.schema = Schema(schema) if schema is not None else None
        self.output_keys = (
            tuple(self.schema.keys()) if self.schema is not None else None
        )
        self._n_backward = ensure_integer(n_backward, "n_backward", min_value=0)
        self._n_forward = ensure_integer(n_forward, "n_forward", min_value=0)
        self._buffer_size = ensure_integer(buffer_size, "buffer_size", min_value=-1)
        # 字段声明仅用于元信息，不参与逐条检查。
        self.used_fields = used_fields

        self._outputs = None
        if self.buffer_size != 0:
            maxlen = None if self.buffer_size == -1 else self.buffer_size
            dtypes = _storage_dtypes(self.schema) if self.schema is not None else None
            self._outputs = DequeTable(maxlen=maxlen, dtypes=dtypes)

        self.g_index = -1
        self._faulted = False

    @property
    def n_backward(self) -> int:
        return self._n_backward

    @property
    def n_forward(self) -> int:
        return self._n_forward

    @property
    def buffer_size(self) -> int:
        return self._buffer_size

    @property
    def min_periods(self) -> int:
        return self.n_backward + 1 + self.n_forward

    @property
    def result_index(self) -> int:
        return self.g_index - self.n_forward

    @property
    def outputs(self) -> Any:
        return self._outputs

    @property
    def meta_info(self) -> dict[str, Any]:
        info = {
            "name": self.name,
            "family": self.family,
            "schema": self.schema,
            "output_keys": self.output_keys,
            "n_backward": self.n_backward,
            "n_forward": self.n_forward,
            "min_periods": self.min_periods,
            "buffer_size": self.buffer_size,
            "g_index": self.g_index,
            "result_index": self.result_index,
        }
        full_name = self.full_name
        if full_name is not None:
            info["full_name"] = full_name
        if self.used_fields is not None:
            info["used_fields"] = self.used_fields
        return info

    def step(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """推进一个新观测；失败后须新建实例并重放。"""
        if self._faulted:
            raise RuntimeError("算子已失效，请新建实例并重放数据")

        # 计算或缓存写入可能部分推进子对象，成功后才解除锁定。
        self._faulted = True
        self.g_index += 1
        result = self.forward(*args, **kwargs)

        if not isinstance(result, dict):
            raise TypeError("forward() 必须返回字典")
        if self.output_keys is None:
            self.output_keys = tuple(result)
            if self._outputs is not None:
                for name in self.output_keys:
                    self._outputs.ensure_column(name, dtype=object)
        elif set(result) != set(self.output_keys):
            raise ValueError(
                f"输出字段不匹配：期望 {self.output_keys}，实际 {tuple(result)}"
            )

        if self._outputs is not None:
            self._outputs.append(result)

        self._faulted = False
        return result

    @abstractmethod
    def forward(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """由具体算子计算一个观测。"""
        raise NotImplementedError


__all__ = ["rOperator"]
