from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from math import isfinite
from typing import Any

from pyta2.utils.validation import ensure_integer

from sigma2.core.utils import forward_step_apply

from .base import rKlineBundleSignal


class rKlineBundleReturnRank(rKlineBundleSignal):
    """按各 symbol 的收盘收益率排名。

    收益率为 close_t / close_(t-lag) - 1，lag 以截面步数计。
    有效收益率按升序或降序稳定排序，从 1 开始依次分配名次；
    收益率相同时，按当前 bundle 的输入顺序排名。

    历史不足、端点缺失、参考价为零或收益率非有限时，排名为 NaN。
    输出格式为 {"rank": {symbol: rank}}。
    """

    name = "ReturnRank"
    input_schema_details = [
        {
            "name": "bundle",
            "type": "mapping",
            "description": "key 是 symbol 字符串，value 是该 symbol 的 K 线",
            "values": {
                "type": "mapping",
                "fields": [
                    {
                        "name": "close",
                        "type": "number",
                        "required": False,
                        "description": "可省略或为 None，按缺失价格处理",
                    },
                    {
                        "name": "is_missing",
                        "type": "bool",
                        "required": False,
                        "description": "可省略，默认为 False",
                    },
                ],
            },
        },
        {"name": "open_time", "description": "K 线截面开盘时间标签，可为 None"},
        {
            "name": "has_missing",
            "type": "bool",
            "description": "收益率排名不使用截面缺失标志",
        },
    ]

    def __init__(
        self,
        lag: int = 1,
        *,
        ascending: bool = True,
        buffer_size: int = 1,
    ) -> None:
        self._lag = ensure_integer(lag, "lag", min_value=1)
        if not isinstance(ascending, bool):
            raise TypeError("ascending must be bool")
        self._ascending = ascending
        super().__init__(
            n_backward=self._lag,
            buffer_size=buffer_size,
        )
        # 每一项属于一个完整截面，避免 symbol 缺席时改变回看时点。
        self._closes = deque(maxlen=self._lag)

    def forward(
        self,
        bundle: Mapping[str, Mapping[str, Any]],
        *,
        open_time: Any = None,
        has_missing: bool = False,
    ) -> dict[str, Any]:
        history = self._closes
        previous = history[0] if len(history) == self._lag else {}
        current = {}
        ranks = dict.fromkeys(bundle, float("nan"))
        returns = []

        for symbol, bar in bundle.items():
            if bar.get("is_missing", False):
                continue
            close = bar.get("close")
            if close is None or not isfinite(close):
                continue
            close = float(close)
            current[symbol] = close
            reference = previous.get(symbol)
            if reference is None or reference == 0:
                continue
            value = close / reference - 1.0
            if isfinite(value):
                returns.append((symbol, value))

        history.append(current)
        returns.sort(key=lambda item: item[1], reverse=not self._ascending)
        for rank, (symbol, _) in enumerate(returns, start=1):
            ranks[symbol] = rank
        return {"rank": ranks}

    @property
    def full_name(self) -> str:
        return f"{self.name}({self._lag},ascending={self._ascending})"


def KlineBundleReturnRank(
    data: Iterable[Mapping[str, Any]],
    lag: int = 1,
    *,
    ascending: bool = True,
    return_type: str = "dict",
    return_meta_info: bool = False,
) -> Any:
    """逐个截面重放收益率排名，返回 symbol 到名次的映射。"""
    return forward_step_apply(
        data,
        rKlineBundleReturnRank(lag=lag, ascending=ascending, buffer_size=0),
        return_type=return_type,
        return_meta_info=return_meta_info,
    )


__all__ = ["KlineBundleReturnRank", "rKlineBundleReturnRank"]
