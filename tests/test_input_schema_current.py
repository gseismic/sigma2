from __future__ import annotations

import pytest

from sigma2 import rBundleSignal, rKlineBundleReturnRank, rKlineSignal, rSignal
from sigma2.orderbook import rOrderBookSignal
from sigma2.trade import rTradeSignal


def test_builtin_input_schemas_describe_actual_entries():
    kline = rKlineSignal.input_schema()["parameters"]
    assert list(kline) == [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "open_time",
        "is_missing",
    ]
    assert kline["close"] == {
        "kind": "positional_or_keyword",
        "required": True,
        "schema": {"type": "number"},
    }
    assert kline["volume"]["default"] is None
    assert kline["volume"]["schema"]["nullable"] is True
    assert kline["open_time"]["kind"] == "keyword_only"
    bundle = rBundleSignal.input_schema()["parameters"]
    assert bundle["bundle"]["schema"]["values"] == {"type": "unknown"}
    assert bundle["time"]["default"] is None
    rank = rKlineBundleReturnRank.input_schema()["parameters"]
    assert set(rank) == {"bundle", "open_time", "has_missing"}
    assert not rank["bundle"]["schema"]["values"]["fields"]["close"]["required"]
    levels = rOrderBookSignal.input_schema()["parameters"]["bids"]["schema"]
    assert levels["items"]["type"] == "tuple"
    assert rTradeSignal.input_schema()["parameters"]["side"]["schema"]["enum"] == [
        "buy",
        "sell",
    ]


def test_signature_defaults_inheritance_and_independent_descriptions():
    default = []

    class Custom(rSignal):
        input_schema_details = {"x": {"type": "string", "enum": ["a", "b"]}}

        def step(self, x, /, optional=default, *args, flag, **kwargs):
            return super().step(x, optional, *args, flag=flag, **kwargs)

        def forward(self, *args, **kwargs):
            return {"value": 1}

    class Inherited(Custom):
        pass

    class Cleared(Custom):
        input_schema_details = {}

    parameters = Inherited.input_schema()["parameters"]
    assert [item["kind"] for item in parameters.values()] == [
        "positional_only",
        "positional_or_keyword",
        "var_positional",
        "keyword_only",
        "var_keyword",
    ]
    assert parameters["optional"]["default"] is default
    assert parameters["flag"]["required"] and not parameters["args"]["required"]
    parameters["x"]["schema"]["enum"].append("changed")
    assert Custom.input_schema()["parameters"]["x"]["schema"]["enum"] == ["a", "b"]
    assert Cleared.input_schema()["parameters"]["x"]["schema"] == {"type": "unknown"}


def test_bad_declarations_are_reported_without_advancing_instance():
    class Broken(rBundleSignal):
        input_schema_details = {"obsolete": {"type": "number"}}

        def forward(self, bundle, *, time=None):
            return {"count": len(bundle)}

    instance = Broken()
    with pytest.raises(ValueError, match="Broken.*obsolete"):
        instance.input_schema()
    assert instance.g_index == -1
    assert instance.step({}) == {"count": 0}

    cyclic = {"type": "sequence"}
    cyclic["items"] = cyclic
    Broken.input_schema_details = {"bundle": cyclic}
    with pytest.raises(ValueError, match=r"Broken.*bundle.*items.*循环"):
        Broken.input_schema()
    Broken.input_schema_details = {"bundle": {"type": "number", "enum": [None]}}
    with pytest.raises(TypeError, match=r"Broken.*bundle.*enum"):
        Broken.input_schema()
