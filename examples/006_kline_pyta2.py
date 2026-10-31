"""pyta2 桥接：将一个 rolling 指标绑定到 K 线字段。"""

from pyta2.stats.sorted_at import rSortedAt
from pyta2.trend.ma.sma import rSMA

from sigma2 import forward_step_apply, pyta2_signal


def main() -> None:
    bars = [
        {"open": close, "high": close, "low": close, "close": close, "open_time": index}
        for index, close in enumerate([10.0, 11.0, 12.0, 15.0])
    ]
    signal = pyta2_signal(rSMA, params={"n": 2}, field="close", history_window=2)
    for bar in bars:
        print("在线指标：", signal.step(**bar))
    print("指标名称和使用字段：", signal.full_name, signal.meta_info["used_fields"])

    fresh = pyta2_signal(rSMA, params={"n": 2}, field="close", history_window=2)
    columns = forward_step_apply(bars, fresh)
    print("批量指标：", columns["ma"])

    # 通用桥接也支持 pyta2 的数组输出。
    ordered = pyta2_signal(rSortedAt, params={"n": 2}, history_window=2)
    for bar in bars:
        print("排序窗口：", ordered.step(**bar)["sorted"])
    print("数组输出缓存：", ordered.outputs["sorted"])
    fresh_ordered = pyta2_signal(rSortedAt, params={"n": 2}, history_window=2)
    print("批量数组输出：", forward_step_apply(bars, fresh_ordered)["sorted"])

    roc = pyta2_signal("ROC", params={"n": 1}, history_window=2)
    print("ROC 批量指标：", forward_step_apply(bars, roc)["roc"])


if __name__ == "__main__":
    main()
