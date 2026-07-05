from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any

from pyta2.base.schema import Schema
from pyta2.utils.deque import DequeTable
from pyta2.utils.space import Space


class rSignal(ABC):
    """轻量有状态 rolling signal 基类。

    生命周期尽量贴近 ``pyta2.base.rIndicator``，但唯一公共状态推进入口
    是 ``step()``。子类只实现 ``forward()``。
    """

    name: str | None = None
    family: str | None = None
    step_input_keys: tuple[str, ...] = ()

    def __init__(
        self,
        window: int,
        schema: list[tuple[str, Space]] | OrderedDict[str, Space] | dict[str, Space] | Schema,
        *,
        buffer_size: int | None = None,
        extra_window: int = 0,
        buffer_factor: int = 2,
        return_dict: bool = False,
        name: str | None = None,
    ) -> None:
        if not isinstance(schema, (list, dict, OrderedDict, Schema)):
            raise TypeError(
                "schema must be list, dict, OrderedDict or Schema, "
                f"got {type(schema)}"
            )
        if buffer_size is not None and buffer_size <= 0:
            raise ValueError(f"buffer_size must be greater than 0, got {buffer_size}")
        if buffer_factor < 1:
            raise ValueError(f"buffer_factor must be at least 1, got {buffer_factor}")
        if name is not None:
            self.name = name

        self.set_window(window, extra_window)
        self.schema = Schema(schema) if isinstance(schema, (list, dict, OrderedDict)) else schema
        self.buffer_factor = buffer_factor
        self.output_keys = list(self.schema.keys())
        self.return_dict = return_dict
        self.g_index = -1
        self._outputs: DequeTable | None = None

        self.resize_buffer(buffer_size)
        self.reset()

    def resize_buffer(self, buffer_size: int | None) -> None:
        """调整短输出缓存容量。"""

        if buffer_size is not None and buffer_size <= 0:
            raise ValueError(f"buffer_size must be greater than 0, got {buffer_size}")

        self.buffer_size = buffer_size
        if self._outputs is None:
            self._outputs = DequeTable(
                maxlen=self.buffer_size,
                dtypes=self.schema.get_dtypes(),
                buffer_factor=self.buffer_factor,
            )
            return

        self._outputs.resize(buffer_size)

    def set_window(self, window: int | None = None, extra_window: int | None = None) -> None:
        """设置 warmup 窗口配置。"""

        if window is not None:
            if window <= 0:
                raise ValueError(f"window must be greater than 0, got {window}")
            self.window = window
        if extra_window is not None:
            if extra_window < 0:
                raise ValueError(
                    "extra_window must be greater than or equal to 0, "
                    f"got {extra_window}"
                )
            self.extra_window = extra_window

    def step(self, *args: Any, **kwargs: Any) -> Any:
        """用一个已确定观测点或事件推进 signal 状态。"""

        self.g_index += 1
        output = self._step_forward(*args, **kwargs)

        dict_output = None
        if self._outputs is not None:
            dict_output = self.make_dict_output(output)
            self._outputs.append(dict_output)

        if self.return_dict:
            if dict_output is None:
                return self.make_dict_output(output)
            return dict_output
        return output

    def _step_forward(self, *args: Any, **kwargs: Any) -> Any:
        return self.forward(*args, **kwargs)

    def reset(self) -> None:
        self.g_index = -1
        if self._outputs is not None:
            self._outputs.clear()
        self.reset_extras()

    @abstractmethod
    def reset_extras(self) -> None:
        """重置子类扩展状态。"""

    @abstractmethod
    def forward(self, *args: Any, **kwargs: Any) -> Any:
        """只计算 signal 值，不推进 core 生命周期。"""

    @property
    @abstractmethod
    def full_name(self) -> str:
        """人可读的 signal 标识。"""

    def make_dict_output(self, output: Any) -> dict[str, Any]:
        """把标量、序列或 mapping 输出标准化到 schema keys。"""

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
            raise TypeError(
                f"{self.full_name} output must not be string-like for schema keys "
                f"{self.output_keys}, got {type(output)}"
            )

        try:
            values = list(output)
        except TypeError as exc:
            raise TypeError(
                f"{self.full_name} output must be iterable for schema keys "
                f"{self.output_keys}, got {type(output)}"
            ) from exc

        if len(values) != len(self.output_keys):
            raise ValueError(
                f"{self.full_name} output arity mismatch: schema keys {self.output_keys}, "
                f"got {len(values)} values from {output!r}"
            )
        return dict(zip(self.output_keys, values))

    def _validate_mapping_keys(self, output: Mapping[str, Any]) -> None:
        expected_keys = set(self.output_keys)
        actual_keys = set(output.keys())
        if actual_keys != expected_keys:
            raise ValueError(
                f"{self.full_name} output keys mismatch: expected {self.output_keys}, "
                f"got {list(output.keys())}"
            )

    @property
    def outputs(self) -> DequeTable | None:
        return self._outputs

    @property
    def latest(self) -> dict[str, Any] | None:
        if self._outputs is None or len(self._outputs) == 0:
            return None
        return self._outputs[-1]

    @property
    def required_window(self) -> int:
        return self.window + self.extra_window

    @property
    def meta_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "full_name": self.full_name,
            "family": self.family,
            "step_input_keys": self.step_input_keys,
            "schema": self.schema,
            "output_keys": self.output_keys,
            "window": self.window,
            "extra_window": self.extra_window,
            "required_window": self.required_window,
            "buffer_size": self.buffer_size,
            "buffer_factor": self.buffer_factor,
            "return_dict": self.return_dict,
            "g_index": self.g_index,
        }
