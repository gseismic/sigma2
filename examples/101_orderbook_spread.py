"""订单簿：计算每个盘口快照的最优买卖价差。"""

from sigma2 import forward_step_apply, rBookSpread


def main() -> None:
    snapshots = [
        {"bids": [(99.5, 3.0), (100.0, 2.0)], "asks": [(100.75, 1.0)]},
        {"bids": [(100.25, 2.0)], "asks": [(101.0, 4.0), (100.75, 1.0)]},
        {"bids": [], "asks": [(100.75, 1.0)]},
    ]
    spread = rBookSpread()
    for snapshot in snapshots:
        print("盘口价差：", spread.step(**snapshot))
    print("使用字段：", spread.meta_info["used_fields"])
    print("批量价差：", forward_step_apply(snapshots, rBookSpread())["spread"])


if __name__ == "__main__":
    main()
