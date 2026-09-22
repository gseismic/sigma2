from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from pyta2.base import rIndicator
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
class _ComponentReference:
    target: Any


@dataclass(frozen=True)
class _DeclaredUpdateState:
    values: dict[str, Any]


@dataclass(frozen=True)
class _FallbackUpdateState:
    values: dict[str, Any]


class rSignal(ABC):
    """轻量有状态 rolling signal 基类。"""

    name: str | None = None
    family: str | None = None
    step_input_keys: tuple[str, ...] = ()
    supports_update_last = True
    # 内置信号应显式声明；None 仅作为第三方/旧子类的兼容兜底。
    _update_state_fields: tuple[str, ...] | None = None

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

    def _apply_pyta2(self, indicator: rIndicator, *args: Any, **kwargs: Any) -> Any:
        """按当前 Signal 生命周期调用 pyta2 子指标。"""

        if not isinstance(indicator, rIndicator):
            raise TypeError(
                f"indicator must be a pyta2 rIndicator instance, got {type(indicator)}"
            )
        if self._lifecycle_mode == _UPDATE_LAST_MODE:
            return indicator.update_last(*args, **kwargs)
        return indicator.rolling(*args, **kwargs)

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
        fields = self._update_state_fields
        if fields is None:
            excluded = self._core_update_state_fields()
            values = {
                key: (
                    _ComponentReference(value)
                    if isinstance(value, (rIndicator, rSignal))
                    else self._snapshot_update_value(value)
                )
                for key, value in self.__dict__.items()
                if key not in excluded
            }
            return _FallbackUpdateState(values)

        values: dict[str, Any] = {}
        for field in fields:
            if not hasattr(self, field):
                raise AttributeError(
                    f"{self.full_name} update state field {field!r} does not exist"
                )
            value = getattr(self, field)
            if isinstance(value, (rIndicator, rSignal)):
                raise TypeError(
                    f"{self.full_name} update state field {field!r} is a lifecycle "
                    "component and must not be checkpointed by its parent"
                )
            values[field] = self._snapshot_update_value(value)
        return _DeclaredUpdateState(values)

    def _restore_update_state(self, state: Any) -> None:
        if isinstance(state, _FallbackUpdateState):
            excluded = self._core_update_state_fields()
            for key in tuple(self.__dict__):
                if key not in excluded:
                    del self.__dict__[key]
            for key, saved in state.values.items():
                if isinstance(saved, _ComponentReference):
                    value = saved.target
                else:
                    value = self._restore_update_value(saved)
                setattr(self, key, value)
            return

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

    @staticmethod
    def _core_update_state_fields() -> set[str]:
        return {
            "g_index",
            "_outputs",
            "_pre_observation_state",
            "_lifecycle_mode",
            "_faulted",
        }

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
