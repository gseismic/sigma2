"""未来边界：以锚点 ATR 为单位扫描后续 K 线。"""

from sigma2 import forward_step_apply, rKlineATRBoundTrigger


def main() -> None:
    bars = [
        {"open": 10, "high": 11, "low": 9, "close": 10, "open_time": 0},
        {"open": 10, "high": 12, "low": 10, "close": 11, "open_time": 1},
        {"open": 11, "high": 14, "low": 11, "close": 13, "open_time": 2},
        {"open": 13, "high": 14, "low": 11, "close": 12, "open_time": 3},
        {"open": 12, "high": 13, "low": 9, "close": 10, "open_time": 4},
    ]
    outcome = rKlineATRBoundTrigger(1, 1, 2, atr_n=2)
    for bar in bars:
        result = outcome.step(**bar)
        if outcome.result_index >= 0:
            print("锚点：", outcome.result_index, "边界结果：", result)

    columns = forward_step_apply(
        bars, rKlineATRBoundTrigger(1, 1, 2, atr_n=2, buffer_size=0)
    )
    print("按锚点回填：", columns)


if __name__ == "__main__":
    main()
