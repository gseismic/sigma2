from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

import numpy as np
from pyta2.base.schema import Schema
from pyta2.utils.deque import DequeTable


class SymbolTable:
    """以 pyta2 标量列存储截面输出，对外恢复时间和 symbol 轴。"""

    def __init__(
        self,
        schema: Schema,
        symbols: tuple[str, ...],
        maxlen: int | None,
        buffer_factor: int,
    ) -> None:
        self.schema = schema
        self.symbols = symbols
        self._shapes = {
            key: (len(symbols), *tuple(getattr(space, "shape", ())))
            for key, space in schema.items()
        }
        self._columns: dict[str, list[str]] = {}
        dtypes: dict[str, Any] = {}
        for field_index, (key, space) in enumerate(schema.items()):
            count = int(np.prod(self._shapes[key], dtype=int))
            columns = [f"{field_index}:{index}" for index in range(count)]
            self._columns[key] = columns
            dtypes.update({column: space.dtype for column in columns})
        self._table = DequeTable(
            maxlen=maxlen, schema=dtypes, buffer_factor=buffer_factor
        )

    def append(self, row: Mapping[str, Any]) -> None:
        flat: dict[str, Any] = {}
        for key, columns in self._columns.items():
            values = np.asarray(row[key], dtype=object)
            if values.shape != self._shapes[key]:
                raise ValueError(
                    f"output {key!r} must have shape {self._shapes[key]}, "
                    f"got {values.shape}"
                )
            flat.update(zip(columns, values.flat))
        self._table.append(flat)

    def __len__(self) -> int:
        return len(self._table)

    def __getitem__(self, key: str | int | slice) -> Any:
        if isinstance(key, str):
            if key not in self._columns:
                raise KeyError(key)
            result = np.empty(
                (len(self), *self._shapes[key]), dtype=self.schema[key].dtype
            )
            flat = (
                result.reshape(len(self), len(self._columns[key]))
                if self._columns[key]
                else None
            )
            if flat is not None:
                for index, column in enumerate(self._columns[key]):
                    flat[:, index] = self._table[column]
            return result
        if isinstance(key, int):
            if key >= len(self) or key < -len(self):
                raise IndexError(key)
            return {name: self[name][key] for name in self._columns}
        if isinstance(key, slice):
            if key.step not in (None, 1):
                raise ValueError("slice step must be 1 or None")
            return {name: self[name][key] for name in self._columns}
        raise TypeError("key must be str, int or slice")

    def __iter__(self) -> Iterator[dict[str, Any]]:
        for index in range(len(self)):
            yield self[index]

    def clear(self) -> None:
        self._table.clear()

    def resize(self, maxlen: int | None) -> None:
        self._table.resize(maxlen)

    def to_dict(self) -> dict[str, Any]:
        return {name: self[name] for name in self._columns}
