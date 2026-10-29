from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from pyta2.base.schema import Schema
from pyta2.utils.deque import DequeTable
from pyta2.utils.validation import ensure_integer


class rOperator(ABC):
    """有状态逐条算子的通用生命周期。

    数据类型实现 step 并调用 _step；具体算子实现 forward。
    """

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
        self.n_backward = ensure_integer(n_backward, "n_backward", min_value=0)
        self.n_forward = ensure_integer(n_forward, "n_forward", min_value=0)
        self.buffer_size = ensure_integer(buffer_size, "buffer_size", min_value=-1)
        # 字段声明仅用于元信息，不参与逐条检查。
        self.used_fields = used_fields

        self._outputs = None
        if self.buffer_size != 0:
            maxlen = None if self.buffer_size == -1 else self.buffer_size
            dtypes = self.schema.get_dtypes() if self.schema is not None else None
            self._outputs = DequeTable(maxlen=maxlen, dtypes=dtypes)

        # 可变计算状态集中存放，以便重算和重置。
        self._state: dict[str, Any] = {}
        # 首次计算前的状态，用于重置。
        self._initial_state: dict[str, Any] | None = None
        # 未确认观测首次计算前的状态；None 表示没有未确认观测。
        self._state_before_pending: dict[str, Any] | None = None
        self._last_observation_id: Any = None
        self.g_index = -1
        self._faulted = False

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

    @abstractmethod
    def step(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """数据类型定义固定输入，并调用 _step 管理生命周期。"""
        raise NotImplementedError("请由数据类型实现 step() 并调用 _step()")

    def _ensure_healthy(self) -> None:
        if self._faulted:
            raise RuntimeError("计算状态异常，请 reset() 后重放数据")

    def _calculate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        result = self.forward(**inputs)
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
        return result

    def _step(
        self,
        inputs: dict[str, Any],
        *,
        is_final: bool = True,
        observation_id: Any = None,
    ) -> dict[str, Any]:
        """根据观测标识和结束状态推进或重算最后一个观测。"""
        self._ensure_healthy()
        if not isinstance(is_final, bool):
            raise TypeError("观测结束状态必须是布尔值")

        if observation_id is not None and self._last_observation_id is not None:
            if observation_id == self._last_observation_id:
                if self._state_before_pending is None:
                    raise ValueError("当前观测已结束；如需修订，请 reset() 后重放数据")
            elif self._state_before_pending is not None:
                raise ValueError("上一条观测尚未结束")

        if self._initial_state is None:
            self._initial_state = deepcopy(self._state)

        if self._state_before_pending is None:
            result = self._advance(inputs, save_state=not is_final)
            self._last_observation_id = observation_id
        else:
            result = self._replace_last(inputs)
            # 中间更新缺少 ID 时保留当前观测已知的 ID。
            if observation_id is not None:
                self._last_observation_id = observation_id

        if is_final:
            self._state_before_pending = None
        return result

    def _advance(self, inputs: dict[str, Any], *, save_state: bool) -> dict[str, Any]:
        """推进新观测；需要修订时保存观测前状态。"""
        checkpoint = deepcopy(self._state) if save_state else None
        previous_index = self.g_index
        self.g_index += 1
        try:
            result = self._calculate(inputs)
            if self._outputs is not None:
                self._outputs.append(result)
        except Exception:
            self.g_index = previous_index
            self._faulted = True
            raise

        self._state_before_pending = checkpoint
        return result

    def _replace_last(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """从原始快照重算最后一个观测，不推进索引。"""
        if self._outputs is not None and len(self._outputs) == 0:
            raise RuntimeError("输出缓存中没有最后一条结果")

        # 每次都从首次计算前的快照恢复，避免重复推进状态。
        restored_state = deepcopy(self._state_before_pending)
        try:
            self._state = restored_state
            result = self._calculate(inputs)
            if self._outputs is not None:
                self._outputs.update_row(-1, result)
        except Exception:
            self._faulted = True
            raise
        return result

    def reset(self) -> None:
        """清理计算状态和输出缓存，重置失败时保持锁定。"""
        self._faulted = True
        if self._initial_state is not None:
            self._state = deepcopy(self._initial_state)
        if self._outputs is not None:
            self._outputs.clear()
        self._state_before_pending = None
        self._last_observation_id = None
        self.g_index = -1
        self._faulted = False

    @abstractmethod
    def forward(self, **inputs: Any) -> dict[str, Any]:
        """计算一个观测；可变计算状态需通过 _state 访问。"""


__all__ = ["rOperator"]
