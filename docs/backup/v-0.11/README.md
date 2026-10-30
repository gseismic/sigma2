# 0.11 旧实现归档

此目录保留本次迁移后不再使用的旧代码和示例，路径对应原仓库位置；归档内容保留原接口，不作为当前可运行示例或公共实现。

- `sigma2/kline/window.py` 和 `_internal/indicator_factor.py`：旧窗口与 pyta2 指标封装，后者含旧 KAMA 特判。
- `sigma2/batch.py`：旧版通用批量重放；当前使用 `forward_step_apply`。
- `sigma2/kline_bundle/`：未适配当前 core 的旧截面实现；当前 Bundle Signal 和价格排名已按新契约重新实现。
- `sigma2/kline/data.py` 和 `_internal/` 中的 `data.py`、`input.py`：旧 K 线对象、字段映射与输入辅助。
- `sigma2/core/identity.py`：旧因子名称拼接工具，当前算子不使用。
- `sigma2/kline/trend/mean_of_mean*.py`：此前删除的两级均值源码，从删除前的 Git 版本恢复到此处。
- `examples/`：已删除的两级均值、Bundle、字段映射和辅助文件，以及拆分前的盘口成交示例。
