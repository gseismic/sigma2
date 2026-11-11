from __future__ import annotations

import numpy as np
import pytest

from sigma2 import Box, Scalar, forward_step_apply, rOutcome, rSignal


class ValueSignal(rSignal):
    def forward(self, value):
        return {"value": value}


class DelayedOutcome(rOutcome):
    def __init__(self, *, buffer_size=1):
        super().__init__(
            n_forward=2,
            schema={"value": Scalar(low=-1000, high=1000, null_value=-99)},
            buffer_size=buffer_size,
        )

    def forward(self, value):
        return {"value": value * 10}


def test_configuration_is_read_only_and_fields_are_copied():
    fields = ["close"]
    signal = ValueSignal(used_fields=fields)
    fields.append("open")
    assert signal.used_fields == ("close",)
    for name, value in (
        ("schema", None),
        ("output_keys", ()),
        ("used_fields", ()),
        ("g_index", 5),
    ):
        with pytest.raises(AttributeError):
            setattr(signal, name, value)
    assert signal.g_index == -1


@pytest.mark.parametrize("buffer_size", [0, 2])
def test_first_output_keys_are_fixed_and_failures_lock(buffer_size):
    class Dynamic(rSignal):
        def forward(self, result):
            return result

    invalid = Dynamic(buffer_size=buffer_size)
    with pytest.raises(TypeError, match="字符串"):
        invalid.step({1: 2})
    assert invalid.g_index == 0
    with pytest.raises(RuntimeError, match="新建实例"):
        invalid.step({"good": 2})

    empty = Dynamic(buffer_size=buffer_size)
    assert empty.step({}) == {}
    assert empty.output_keys == ()
    with pytest.raises(ValueError, match="输出字段不匹配"):
        empty.step({"later": 1})
    with pytest.raises(RuntimeError, match="新建实例"):
        empty.step({})


def test_online_and_batch_share_types_and_declared_field_order():
    scalar = Scalar(low=-100, high=100, dtype=np.float64, null_value=-99)
    schema = {
        "scalar": scalar,
        "optional": Scalar(low=-100, high=100, null_value=None),
        "vector": Box(low=0, high=10, shape=(2,)),
    }

    class MultiOutput(rSignal):
        def forward(self, value):
            return {
                "vector": np.array([value, value + 1]),
                "optional": None,
                "scalar": value,
            }

    signal = MultiOutput(schema=schema, buffer_size=2)
    # 不支持原地修改 Space，但已确定的在线与批量配置不能各自重新解释它。
    scalar.null_value = None
    scalar.dtype = np.int32
    rows = [{"value": 1}, {"value": 2}]
    result = forward_step_apply(rows, signal)
    assert list(result) == signal.outputs.columns == ["scalar", "optional", "vector"]
    assert (
        result["scalar"].dtype == signal.outputs.dtypes["scalar"] == np.dtype("float64")
    )
    assert result["optional"].dtype == result["vector"].dtype == np.dtype(object)
    assert list(result["optional"]) == [None, None]
    np.testing.assert_array_equal(result["vector"][1], [2, 3])


def test_schema_free_object_results_keep_published_references():
    array = np.array([1.0, 2.0])
    signal = ValueSignal(buffer_size=2)
    output = forward_step_apply([{"value": array}, {"value": None}], signal)
    assert output["value"].dtype == signal.outputs.dtypes["value"] == np.dtype(object)
    assert output["value"][0] is signal.outputs["value"][0] is array
    assert output["value"][1] is None


def test_outcome_batch_alignment_and_existing_instance_replay():
    outcome = DelayedOutcome(buffer_size=-1)
    outcome.step(0)
    outcome.step(1)
    outcome.schema["value"].null_value = None
    output = forward_step_apply([{"value": 2}, {"value": 3}, {"value": 4}], outcome)
    assert list(output["value"]) == [40.0, -99.0, -99.0]
    assert list(outcome.outputs["value"]) == [0.0, 10.0, 20.0, 30.0, 40.0]
    assert outcome.g_index == 4 and outcome.result_index == 2


def test_empty_replay_and_preflight_do_not_advance_or_consume():
    plain = ValueSignal()
    plain.step(3)
    assert forward_step_apply([], plain) == {}
    assert plain.g_index == 0
    outcome = DelayedOutcome()
    result = forward_step_apply([], outcome)
    assert list(result) == ["value"] and len(result["value"]) == 0
    assert outcome.g_index == -1

    def rows():
        raise AssertionError("不应消费输入")
        yield {"value": 1}

    with pytest.raises(ValueError):
        forward_step_apply(rows(), plain, return_type="unsupported")
    assert plain.g_index == 0

    def interrupted_rows():
        yield {"value": 4}
        raise ValueError("输入中断")

    with pytest.raises(ValueError, match="输入中断"):
        forward_step_apply(interrupted_rows(), plain)
    assert plain.g_index == 1


def test_input_binding_and_online_cache_failure_have_distinct_boundaries():
    class FixedEntry(rSignal):
        def step(self, value):
            return super().step(value)

        def forward(self, value):
            return {"value": value}

    signal = FixedEntry(schema={"value": Scalar(low=-10, high=10)})
    with pytest.raises(TypeError):
        signal.step()
    assert signal.g_index == -1
    with pytest.raises((TypeError, ValueError)):
        signal.step("无法转为数值")
    assert signal.g_index == 0
    with pytest.raises(RuntimeError, match="新建实例"):
        signal.step(1)
