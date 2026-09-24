from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import DTypeLike
from pyta2.base.schema import Schema
from pyta2.utils.deque import DequeTable
from pyta2.utils.space import Space


_NO_UPDATE_STATE = object()
_STEP_MODE = "step"
_UPDATE_LAST_MODE = "update_last"


@dataclass(frozen=True)
class _ObjectUpdateState:
    target: Any
    checkpoint: Any


@dataclass(frozen=True)
class _CopiedUpdateState:
    value: Any


@dataclass(frozen=True)
class _DeclaredUpdateState:
    values: dict[str, Any]


@dataclass(frozen=True)
class _DTypeField:
    dtype: np.dtype[Any]


class _DTypeSchema(Mapping[str, Space | _DTypeField]):
    """只声明 dtype 的输出 schema；保留 pyta2 Space 的兼容入口。"""

    def __init__(self, entries: list[tuple[str, Any]]) -> None:
        fields: OrderedDict[str, Space | _DTypeField] = OrderedDict()
        if not entries:
            raise ValueError("schema must contain at least one field")
        for entry in entries:
            if not isinstance(entry, (list, tuple)) or len(entry) != 2:
                raise TypeError(
                    f"schema entries must be (key, dtype) pairs, got {entry!r}"
                )
            key, spec = entry
            if not isinstance(key, str):
                raise ValueError(f"schema key must be str, got {type(key)}")
            if key in fields:
                raise ValueError(
                    f"schema key must be unique, got duplicate key {key!r}"
                )
            if isinstance(spec, Space):
                fields[key] = spec
                continue
            if spec is None:
                raise TypeError(f"schema dtype for {key!r} must not be None")
            try:
                fields[key] = _DTypeField(np.dtype(spec))
            except (TypeError, ValueError) as exc:
                raise TypeError(
                    f"schema dtype for {key!r} is invalid: {spec!r}"
                ) from exc
        self._fields = fields

    def __getitem__(self, key: str) -> Space | _DTypeField:
        return self._fields[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._fields)

    def __len__(self) -> int:
        return len(self._fields)

    def get_dtypes(self) -> dict[str, DTypeLike]:
        return {key: field.dtype for key, field in self._fields.items()}


def _normalize_schema(
    schema: list[tuple[str, Space | DTypeLike]]
    | Mapping[str, Space | DTypeLike]
    | Schema
    | _DTypeSchema,
) -> Schema | _DTypeSchema:
    if isinstance(schema, (Schema, _DTypeSchema)):
        return schema
    if isinstance(schema, Mapping):
        entries = list(schema.items())
    elif isinstance(schema, list):
        entries = list(schema)
    else:
        raise TypeError(f"schema must be list, Mapping or Schema, got {type(schema)}")
    if entries and all(
        isinstance(entry, (list, tuple))
        and len(entry) == 2
        and isinstance(entry[1], Space)
        for entry in entries
    ):
        return Schema(schema)
    return _DTypeSchema(entries)


class rSignal(ABC):
    """轻量有状态 rolling signal 基类；schema 可用 Space 或 NumPy dtype。"""

    name: str | None = None
    family: str | None = None
    step_input_keys: tuple[str, ...] = ()
    supports_update_last = True
    # 新子类声明需要在 update_last 前恢复的自有字段；None 沿用旧入口。
    checkpoint_fields: tuple[str, ...] | None = None
    # 有额外递推状态的子类应显式列出需要修订的字段。
    _update_state_fields: tuple[str, ...] = ()

    def __init__(
        self,
        window: int,
        schema: list[tuple[str, Space | DTypeLike]]
        | Mapping[str, Space | DTypeLike]
        | Schema,
        *,
        buffer_size: int | None = None,
        extra_window: int = 0,
        buffer_factor: int = 2,
        return_dict: bool = False,
        name: str | None = None,
    ) -> None:
        if buffer_size is not None and buffer_size <= 0:
            raise ValueError(f"buffer_size must be greater than 0, got {buffer_size}")
        if buffer_factor < 1:
            raise ValueError(f"buffer_factor must be at least 1, got {buffer_factor}")
        if name is not None:
            self.name = name

        self.set_window(window, extra_window)
        self.schema = _normalize_schema(schema)
        self.buffer_factor = buffer_factor
        self.output_keys = list(self.schema.keys())
        self.return_dict = return_dict
        self.g_index = -1
        self._outputs: DequeTable | None = None
        self._pre_observation_state: Any = _NO_UPDATE_STATE
        self._lifecycle_mode: str | None = None
        self._faulted = False

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

    def set_window(
        self, window: int | None = None, extra_window: int | None = None
    ) -> None:
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
        """输入一个新的逻辑观测并推进 signal 状态。"""

        self._ensure_healthy()
        previous_index = self.g_index
        self._pre_observation_state = self._snapshot_update_state()
        self.g_index = previous_index + 1
        previous_mode = self._lifecycle_mode
        self._lifecycle_mode = _STEP_MODE
        try:
            output = self._step_forward(*args, **kwargs)
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

    def update_last(self, *args: Any, **kwargs: Any) -> Any:
        """修订最后一个逻辑观测，不推进时间索引。"""

        self._ensure_healthy()
        if not self.supports_update_last:
            raise NotImplementedError(
                f"{self.full_name} does not support update_last(); reset and replay instead"
            )
        if self.g_index < 0 or self._pre_observation_state is _NO_UPDATE_STATE:
            raise IndexError(
                f"{self.full_name} update_last() requires a preceding step() call"
            )

        previous_mode = self._lifecycle_mode
        try:
            self._restore_update_state(self._pre_observation_state)
            self._lifecycle_mode = _UPDATE_LAST_MODE
            output = self._update_last_forward(*args, **kwargs)
            dict_output = self.make_dict_output(output)
            if self._outputs is not None:
                if len(self._outputs) == 0:
                    raise RuntimeError(
                        f"{self.full_name} cannot replace an empty output cache"
                    )
                self._outputs.update_row(-1, dict_output)
        except Exception:
            self._faulted = True
            raise
        finally:
            self._lifecycle_mode = previous_mode

        return dict_output if self.return_dict else output

    def _step_forward(self, *args: Any, **kwargs: Any) -> Any:
        return self.forward(*args, **kwargs)

    def _update_last_forward(self, *args: Any, **kwargs: Any) -> Any:
        return self.forward(*args, **kwargs)

    def apply_component(self, component: Any, *args: Any, **kwargs: Any) -> Any:
        """按当前生命周期调用子组件的 step() 或 update_last()。"""

        self._ensure_healthy()
        if self._lifecycle_mode not in {_STEP_MODE, _UPDATE_LAST_MODE}:
            raise RuntimeError(
                "apply_component() requires an active step() or update_last() call"
            )
        step = getattr(component, "step", None)
        update_last = getattr(component, "update_last", None)
        if not callable(step) or not callable(update_last):
            raise TypeError(
                "component must implement callable step() and update_last() methods, "
                f"got {type(component)}"
            )
        if self._lifecycle_mode == _UPDATE_LAST_MODE:
            return update_last(*args, **kwargs)
        return step(*args, **kwargs)

    def reset(self) -> None:
        self.g_index = -1
        self._pre_observation_state = _NO_UPDATE_STATE
        self._lifecycle_mode = None
        self._faulted = False
        if self._outputs is not None:
            self._outputs.clear()
        self.reset_extras()

    def _ensure_healthy(self) -> None:
        if self._faulted:
            raise RuntimeError(
                f"{self.full_name} is faulted after a failed state calculation; "
                "call reset() and replay committed observations"
            )

    def _snapshot_update_state(self) -> Any:
        fields = (
            self._update_state_fields
            if self.checkpoint_fields is None
            else self.checkpoint_fields
        )
        if not isinstance(fields, tuple) or any(
            not isinstance(field, str) for field in fields
        ):
            raise TypeError(
                f"{self.full_name} checkpoint_fields must be a tuple of field names"
            )
        values: dict[str, Any] = {}
        for field in fields:
            if not hasattr(self, field):
                raise AttributeError(
                    f"{self.full_name} update state field {field!r} does not exist"
                )
            value = getattr(self, field)
            if isinstance(value, rSignal) or (
                callable(getattr(value, "update_last", None))
                and callable(getattr(value, "reset", None))
            ):
                raise TypeError(
                    f"{self.full_name} update state field {field!r} is a lifecycle "
                    "component and must not be checkpointed by its parent"
                )
            values[field] = self._snapshot_update_value(value)
        return _DeclaredUpdateState(values)

    def _restore_update_state(self, state: Any) -> None:
        if not isinstance(state, _DeclaredUpdateState):
            raise TypeError(f"{self.full_name} has an invalid update checkpoint")
        for field, saved in state.values.items():
            setattr(self, field, self._restore_update_value(saved))

    @staticmethod
    def _snapshot_update_value(value: Any) -> Any:
        if isinstance(value, (type(None), bool, int, float, complex, str, bytes)):
            return value
        make_checkpoint = getattr(value, "_make_update_checkpoint", None)
        if callable(make_checkpoint):
            return _ObjectUpdateState(value, make_checkpoint())
        return _CopiedUpdateState(deepcopy(value))

    @staticmethod
    def _restore_update_value(state: Any) -> Any:
        if isinstance(state, _ObjectUpdateState):
            restore = getattr(state.target, "_restore_update_checkpoint", None)
            if not callable(restore):
                raise TypeError("checkpoint target does not support restore")
            restore(state.checkpoint)
            return state.target
        if isinstance(state, _CopiedUpdateState):
            return deepcopy(state.value)
        return state

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
            "window": self.window,
            "extra_window": self.extra_window,
            "required_window": self.required_window,
            "factor_names": self.factor_names,
            "buffer_size": self.buffer_size,
            "buffer_factor": self.buffer_factor,
            "return_dict": self.return_dict,
            "g_index": self.g_index,
            "supports_update_last": self.supports_update_last,
            "is_faulted": self.is_faulted,
        }
