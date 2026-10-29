"""趋势指标：逐条计算 MACD 和均线交叉。"""

from sigma2 import rKlineMACD, rKlineMACross


def main() -> None:
    macd = rKlineMACD(fast=2, slow=4, signal=2)
    cross = rKlineMACross(2, 4, ma_type="EMA")
    closes = [10, 11, 12, 11, 9, 10, 13, 14]
    for index, close in enumerate(closes):
        bar = {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "open_time": index,
        }
        print(index, "MACD:", macd.step(**bar), "均线交叉:", cross.step(**bar))
    print("公式：", macd.full_name, cross.full_name)


if __name__ == "__main__":
    main()
