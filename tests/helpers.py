"""为测试构造按时间排序的单 symbol K 线。"""

from datetime import datetime, timedelta, timezone
from itertools import count

from sigma2.kline import KlineBar


_counter = count()
_start = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_bar(*, open, high, low, close, volume=1.0, symbol="A"):
    return KlineBar(
        symbol,
        _start + timedelta(seconds=next(_counter)),
        open,
        high,
        low,
        close,
        volume,
    )


def bars_from_columns(data, *, symbol="A"):
    return [
        KlineBar(
            symbol,
            _start + timedelta(seconds=index),
            *(data[key][index] for key in ("open", "high", "low", "close", "volume")),
        )
        for index in range(len(data["close"]))
    ]
