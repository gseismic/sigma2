from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from pyta2.base.schema import Schema
from pyta2.utils.deque import DequeTable
from pyta2.utils.space import Space
from pyta2.utils.validation import ensure_integer


class rOperator(ABC):
    """逐条推进的有状态算子，统一预热、结果位置和输出生命周期。"""

    name: str | None = None
    family: str | None = None
    step_input_keys: tuple[str, ...] = ()

    def __init__(
        self,
        schema: list[tuple[str, Space]] | Mapping[str, Space] | Schema,
        *,
        n_backward: int,
        n_forward: int,
        buffer_size: int | None = 1,
        buffer_factor: int = 2,
        return_dict: bool = False,
    ) -> None:
        if not isinstance(schema, (list, Mapping, Schema)):
            raise TypeError(
                f"schema must be list, Mapping or Schema, got {type(schema)}"
            )
        self._n_backward = ensure_integer(n_backward, "n_backward", min_value=0)
        self._n_forward = ensure_integer(n_forward, "n_forward", min_value=0)
        if not isinstance(return_dict, bool):
            raise TypeError(
                f"return_dict must be bool, got {type(return_dict).__name__}"
            )
        self.schema = Schema(schema) if isinstance(schema, (list, Mapping)) else schema
        self.output_keys = list(self.schema.keys())
        self.buffer_factor = buffer_factor
        self.return_dict = return_dict
        self.g_index = -1
        self._outputs: Any = None
        self._faulted = False
        self._lifecycle_mode: str | None = None
        self.resize_buffer(buffer_size)
        self.reset()

    @property
    def n_backward(self) -> int:
        return self._n_backward

    @property
    def n_forward(self) -> int:
        return self._n_forward

    @property
    def min_periods(self) -> int:
        return self.n_backward + 1 + self.n_forward

    @property
    def result_index(self) -> int:
        return self.g_index - self.n_forward

    def _new_output_table(self, maxlen: int | None) -> Any:
        return DequeTable(
            maxlen=maxlen,
            dtypes=self.schema.get_dtypes(),
            buffer_factor=self.buffer_factor,
        )

    def resize_buffer(self, buffer_size: int | None) -> None:
        """调整输出缓存；0/None 关闭，-1 表示无限。"""
        size = ensure_integer(buffer_size, "buffer_size", min_value=-1, allow_none=True)
        size = 0 if size is None else size
        self.buffer_size = size
        if size == 0:
            self._outputs = None
            return
        maxlen = None if size == -1 else size
        if self._outputs is None:
            self._outputs = self._new_output_table(maxlen)
        else:
            self._outputs.resize(maxlen)

    def step(self, *args: Any, **kwargs: Any) -> Any:
        """推进一个逻辑观测，失败后锁定实例，避免继续使用部分状态。"""
        self._ensure_healthy()
        previous_index = self.g_index
        self.g_index += 1
        previous_mode = self._lifecycle_mode
        self._lifecycle_mode = "step"
        try:
            output = self._step_forward(*args, **kwargs)
            dict_output = None
            if self._outputs is not None or self.return_dict:
                dict_output = self.make_dict_output(output)
            if self._outputs is not None:
                self._outputs.append(dict_output)
        except Exception:
            self.g_index = previous_index
            self._faulted = True
            raise
        finally:
            self._lifecycle_mode = previous_mode
        return dict_output if self.return_dict else output

    def _step_forward(self, *args: Any, **kwargs: Any) -> Any:
        return self.forward(*args, **kwargs)

    def reset(self) -> None:
        """清除全部运行状态；重置失败时继续锁定实例。"""
        self._faulted = True
        try:
            self.g_index = -1
            self._lifecycle_mode = None
            if self._outputs is not None:
                self._outputs.clear()
            self.reset_extras()
        except Exception:
            self._faulted = True
            raise
        self._faulted = False

    def reset_extras(self) -> None:
        """子类需要时重置自己的状态或子算子。"""

    def _ensure_healthy(self) -> None:
        if self._faulted:
            raise RuntimeError(
                f"{self.full_name} is faulted; call reset() and replay confirmed inputs"
            )

    @abstractmethod
    def forward(self, *args: Any, **kwargs: Any) -> Any:
        """计算钩子；调用方通过 step 推进生命周期。"""

    @property
    @abstractmethod
    def full_name(self) -> str:
        """含参数的计算身份。"""

    def make_dict_output(self, output: Any) -> dict[str, Any]:
        """按 pyta2 语义将原始结果转换为 schema 字段映射。"""
        if len(self.output_keys) == 1:
            key = self.output_keys[0]
            if isinstance(output, Mapping):
                self._validate_mapping_keys(output)
                return {key: output[key]}
            return {key: output}
        if isinstance(output, Mapping):
            self._validate_mapping_keys(output)
            return {key: output[key] for key in self.output_keys}
        if isinstance(output, (str, bytes, bytearray)):
            raise TypeError(f"{self.full_name} output must not be string-like")
        try:
            values = list(output)
        except TypeError as exc:
            raise TypeError(f"{self.full_name} output must be iterable") from exc
        if len(values) != len(self.output_keys):
            raise ValueError(
                f"{self.full_name} output arity mismatch: schema keys "
                f"{self.output_keys}, got {len(values)} values"
            )
        return dict(zip(self.output_keys, values))

    def _validate_mapping_keys(self, output: Mapping[str, Any]) -> None:
        if set(output) != set(self.output_keys):
            raise ValueError(
                f"{self.full_name} output keys mismatch: expected {self.output_keys}, "
                f"got {list(output)}"
            )

    @property
    def missing_output(self) -> Any:
        values = [self.schema[name].null_value for name in self.output_keys]
        return values[0] if len(values) == 1 else tuple(values)

    @property
    def outputs(self) -> Any:
        return self._outputs

    @property
    def latest(self) -> dict[str, Any] | None:
        if self._outputs is None or len(self._outputs) == 0:
            return None
        return self._outputs[-1]

    @property
    def factor_names(self) -> list[str]:
        if len(self.output_keys) == 1:
            return [self.full_name]
        return [f"{self.full_name}.{key}" for key in self.output_keys]

    @property
    def is_faulted(self) -> bool:
        return self._faulted

    @property
    def meta_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "full_name": self.full_name,
            "family": self.family,
            "step_input_keys": self.step_input_keys,
            "schema": self.schema,
            "output_keys": self.output_keys,
            "n_backward": self.n_backward,
            "n_forward": self.n_forward,
            "min_periods": self.min_periods,
            "result_index": self.result_index,
            "factor_names": self.factor_names,
            "buffer_size": self.buffer_size,
            "buffer_factor": self.buffer_factor,
            "return_dict": self.return_dict,
            "g_index": self.g_index,
            "is_faulted": self.is_faulted,
        }


class rSignal(rOperator):
    """结果属于当前观测的算子；未来期固定为零。"""

    def __init__(self, schema: Any, *, n_backward: int, **kwargs: Any) -> None:
        super().__init__(schema, n_backward=n_backward, n_forward=0, **kwargs)


class rOutcome(rOperator):
    """等待固定后续观测后，输出属于历史锚点的结果。"""

    def __init__(
        self, schema: Any, *, n_backward: int, n_forward: int, **kwargs: Any
    ) -> None:
        n_forward = ensure_integer(n_forward, "n_forward", min_value=1)
        super().__init__(schema, n_backward=n_backward, n_forward=n_forward, **kwargs)


__all__ = ["rOperator", "rSignal", "rOutcome"]
