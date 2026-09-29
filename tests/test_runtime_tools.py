import pandas as pd

from evidence_first.adapters.scripted import ScriptedAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.result import AgentDecision, AgentResult
from evidence_first.runtime import InvestigationEngine, Stage, ToolExecutionBroker
from evidence_first.tools.factory import dataframe_registry
from tests.runtime_fixtures import secure_handlers


def test_evidence_analyst_tool_loop_executes_and_reruns():
    calls = {"n": 0}

    def analyst(spec, context):
        calls["n"] += 1
        if "tool_outcomes" not in context:
            return AgentResult(
                spec.role,
                AgentDecision.CONTINUE,
                "need profile",
                {
                    "tool_requests": [
                        {"name": "dataframe.profile", "arguments": {}}
                    ]
                },
            )
        return AgentResult(
            spec.role,
            AgentDecision.CONTINUE,
            "analyzed",
            {
                "segmentation_results": {},
                "analysis_results": {
                    "tool_outcomes": context["tool_outcomes"]
                },
                "derived_evidence": [
                    {
                        "evidence_id": "e1",
                        "statement": "Primary mechanism matches the affected segment.",
                        "kind": "observation",
                        "source": "test",
                        "reliability": 1.0,
                    },
                    {
                        "evidence_id": "e2",
                        "statement": "Alternative mechanism is contradicted.",
                        "kind": "observation",
                        "source": "test",
                        "reliability": 1.0,
                    },
                ],
                "hypothesis_tests": [
                    {
                        "hypothesis_id": "h1",
                        "evidence_for": ["e1"],
                        "evidence_against": [],
                    },
                    {
                        "hypothesis_id": "h2",
                        "evidence_for": [],
                        "evidence_against": ["e2"],
                    },
                ],
                "tool_requests": [],
                "method_limits": [],
            },
        )

    handlers = secure_handlers()
    handlers[AgentRole.EVIDENCE_ANALYST] = analyst
    broker = ToolExecutionBroker(
        dataframe_registry(pd.DataFrame({"x": [1, 2]}))
    )
    run = InvestigationEngine(
        ScriptedAdapter(handlers),
        tool_broker=broker,
    ).run("why")

    assert run.stage is Stage.AWAITING_OUTCOME
    assert calls["n"] == 2
    assert any(e.event_type == "tools_executed" for e in run.events)
