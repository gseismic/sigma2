"""未来收益目标按历史 anchor 对齐：运行 python -m examples.future_target。"""

from sigma2.kline.target import rKlineFutureReturn


def main() -> None:
    target = rKlineFutureReturn(2, return_dict=True)
    for current_index, close in enumerate([10.0, 11.0, 13.0, 12.0]):
        result = target.step(open=close, high=close, low=close, close=close, volume=1.0)
        anchor_index = current_index - target.horizon
        if anchor_index >= 0:
            print(
                f"当前索引 {current_index} 确定了索引 {anchor_index} 的目标：{result['return']:.4f}"
            )


if __name__ == "__main__":
    main()
