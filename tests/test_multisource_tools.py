from __future__ import annotations

import pandas as pd

from evidence_first.runtime import ToolExecutionBroker, ToolRequest
from evidence_first.tools.multisource import multisource_dataframe_registry


def test_multisource_tool_dispatches_by_source_id():
    registry = multisource_dataframe_registry(
        {
            "a.csv": pd.DataFrame({"site": ["A", "B"], "sla": [90, 80]}),
            "b.csv": pd.DataFrame({"site": ["A", "B"], "sla": [70, 60]}),
        }
    )
    broker = ToolExecutionBroker(
        registry,
        trusted_source_ids={"a.csv", "b.csv"},
    )

    a = broker.execute(
        ToolRequest(
            "dataframe.group_metric",
            {
                "source_id": "a.csv",
                "group": "site",
                "metric": "sla",
                "agg": "mean",
            },
            ("a.csv",),
        )
    )
    b = broker.execute(
        ToolRequest(
            "dataframe.group_metric",
            {
                "source_id": "b.csv",
                "group": "site",
                "metric": "sla",
                "agg": "mean",
            },
            ("b.csv",),
        )
    )

    assert a.ok and b.ok
    assert a.value.value["A"] == 90.0
    assert b.value.value["A"] == 70.0
    assert a.source_ids == ("a.csv",)


def test_multisource_tool_rejects_unknown_source():
    registry = multisource_dataframe_registry(
        {"a.csv": pd.DataFrame({"x": [1, 2]})}
    )
    broker = ToolExecutionBroker(registry)
    outcome = broker.execute(
        ToolRequest("dataframe.profile", {"source_id": "missing.csv"})
    )
    assert not outcome.ok
    assert "KeyError" in outcome.error
