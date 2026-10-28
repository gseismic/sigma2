"""未来收益属于历史锚点：运行 python -m examples.04_future_outcome。"""

from examples._data import make_bars
from sigma2 import forward_outcome_apply, rKlineFutureReturn


def main() -> None:
    bars = make_bars([10.0, 11.0, 13.0, 12.0])
    outcome = rKlineFutureReturn(2, return_dict=True)
    for bar in bars:
        result = outcome.step(bar)
        if outcome.result_index >= 0:
            print(
                f"当前步 {outcome.g_index}，结果属于 {outcome.result_index}：{result['return']:.4f}"
            )
    columns = forward_outcome_apply(bars, rKlineFutureReturn, param_args=(2,))
    print("按锚点回填：", columns)


if __name__ == "__main__":
    main()
