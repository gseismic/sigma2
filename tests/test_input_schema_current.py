from __future__ import annotations

import pytest

from sigma2 import (
    rBundleSignal,
    rKlineBundleMarketCapWeightedIndex,
    rKlineBundleReturnRank,
    rKlineSignal,
    rSignal,
)
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
    assert "None" in kline["volume"]["schema"]["description"]
    assert kline["open_time"]["kind"] == "keyword_only"

    bundle = rBundleSignal.input_schema()["parameters"]
    assert bundle["bundle"]["schema"]["values"] == {"type": "unknown"}
    assert bundle["time"]["default"] is None
    rank = rKlineBundleReturnRank.input_schema()["parameters"]
    assert set(rank) == {"bundle", "open_time", "has_missing"}
    fields = rank["bundle"]["schema"]["values"]["fields"]
    assert [field["name"] for field in fields] == ["close", "is_missing"]
    assert fields[0]["required"] is False and "None" in fields[0]["description"]
    cap = rKlineBundleMarketCapWeightedIndex.input_schema()["parameters"]
    assert "market_cap" in [
        field["name"] for field in cap["bundle"]["schema"]["values"]["fields"]
    ]
    levels = rOrderBookSignal.input_schema()["parameters"]["bids"]["schema"]
    assert levels["items"]["type"] == "tuple"
    assert (
        "buy"
        in rTradeSignal.input_schema()["parameters"]["side"]["schema"]["description"]
    )


def test_signature_defaults_inheritance_and_nested_description_copy():
    default = []

    class Custom(rSignal):
        input_schema_details = [
            {
                "name": "x",
                "type": "mapping",
                "values": {
                    "type": "list",
                    "items": {
                        "type": "custom",
                        "fields": [{"name": "price", "type": "number"}],
                    },
                },
                "说明": "自由元数据",
            }
        ]

        def step(self, x, /, optional=default, *args, flag, **kwargs):
            return super().step(x, optional, *args, flag=flag, **kwargs)

        def forward(self, *args, **kwargs):
            return {"value": 1}

    class Inherited(Custom):
        pass

    class Cleared(Custom):
        input_schema_details = []

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
    schema = parameters["x"]["schema"]
    assert schema["说明"] == "自由元数据"
    schema["values"]["items"]["fields"][0]["name"] = "changed"
    fresh = Custom.input_schema()["parameters"]["x"]["schema"]
    assert fresh["values"]["items"]["fields"][0]["name"] == "price"
    assert Cleared.input_schema()["parameters"]["x"]["schema"] == {"type": "unknown"}


def test_top_level_declaration_errors_do_not_advance_instance():
    class Broken(rBundleSignal):
        input_schema_details = [{"name": "obsolete", "type": "number"}]

        def forward(self, bundle, *, time=None):
            return {"count": len(bundle)}

    instance = Broken()
    with pytest.raises(ValueError, match="Broken.*obsolete"):
        instance.input_schema()
    assert instance.g_index == -1
    assert instance.step({}) == {"count": 0}

    Broken.input_schema_details = [{"name": "bundle"}, {"name": "bundle"}]
    with pytest.raises(ValueError, match="重复"):
        Broken.input_schema()
    Broken.input_schema_details = [{"name": "bundle", "required": False}]
    with pytest.raises(ValueError, match="签名决定"):
        Broken.input_schema()
