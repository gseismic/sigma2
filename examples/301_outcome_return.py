"""未来收益：按当前步输出，并按历史锚点批量回填。"""

from sigma2 import forward_step_apply, rKlineFutureReturn


def main() -> None:
    closes = [10.0, 11.0, 13.0, 12.0]
    bars = [
        {"open": close, "high": close, "low": close, "close": close, "open_time": index}
        for index, close in enumerate(closes)
    ]
    outcome = rKlineFutureReturn(2)
    for bar in bars:
        result = outcome.step(**bar)
        if outcome.result_index >= 0:
            print(
                f"当前步 {outcome.g_index}，结果属于 {outcome.result_index}："
                f"{result['return']:.4f}"
            )
    columns = forward_step_apply(bars, rKlineFutureReturn(2, buffer_size=0))
    print("按锚点回填：", columns["return"])


if __name__ == "__main__":
    main()
