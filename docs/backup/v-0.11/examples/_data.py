"""示例使用的小规模、已确认的日 K 线。"""

from datetime import datetime, timedelta, timezone

from sigma2.kline import KlineBar


def make_bars(closes, symbol="A"):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        KlineBar(
            symbol=symbol,
            bar_time=start + timedelta(days=index),
            open=close,
            high=close + 0.5,
            low=close - 0.5,
            close=close,
            volume=100.0 + 10 * index,
            available_at=start + timedelta(days=index + 1),
        )
        for index, close in enumerate(closes)
    ]


def make_bundles(rows, symbols=("A", "B")):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bundles = []
    for index, row in enumerate(rows):
        bar_time = start + timedelta(days=index)
        available_at = bar_time + timedelta(days=1)
        bars = {
            symbol: {
                "symbol": symbol,
                "open": close,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "volume": 100.0,
            }
            for symbol, close in row.items()
        }
        bundles.append(
            {
                "open_time": bar_time,
                "symbols": symbols,
                "bundle": bars,
                "available_at": available_at,
            }
        )
    return bundles
