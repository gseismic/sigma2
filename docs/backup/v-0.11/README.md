# 0.11 旧实现归档

此目录保留本次迁移后不再使用的旧代码和示例，路径对应原仓库位置；归档内容保留原接口，不作为当前可运行示例或公共实现。

- `sigma2/kline/window.py` 和 `_internal/indicator_factor.py`：旧窗口与 pyta2 指标封装，后者含旧 KAMA 特判。
- `sigma2/kline/trend/mean_of_mean*.py`：此前删除的两级均值源码，从删除前的 Git 版本恢复到此处。
- `examples/`：已删除的两级均值、Bundle、字段映射和辅助文件，以及拆分前的盘口成交示例。Bundle 尚待迁移。
