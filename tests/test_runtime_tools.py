import pandas as pd
from evidence_first.adapters.scripted import ScriptedAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.result import AgentDecision,AgentResult
from evidence_first.runtime import InvestigationEngine,Stage,ToolExecutionBroker
from evidence_first.tools.factory import dataframe_registry

def generic(spec,context):
    outputs=spec.outputs
    artifact=outputs[0] if outputs else "result"
    return AgentResult(spec.role,AgentDecision.CONTINUE,"ok",{artifact:{"ok":True}})

def test_evidence_analyst_tool_loop_executes_and_reruns():
    calls={"n":0}
    def analyst(spec,context):
        calls["n"]+=1
        if "tool_outcomes" not in context:
            return AgentResult(spec.role,AgentDecision.CONTINUE,"need profile",{"tool_requests":[{"name":"dataframe.profile","arguments":{}}]})
        return AgentResult(spec.role,AgentDecision.CONTINUE,"analyzed",{"analysis_results":{"tool_outcomes":context["tool_outcomes"]},"hypothesis_tests":{},"segmentation_results":{},"derived_evidence":[],"method_limits":[]})
    handlers={r:generic for r in AgentRole}
    handlers[AgentRole.EVIDENCE_ANALYST]=analyst
    broker=ToolExecutionBroker(dataframe_registry(pd.DataFrame({"x":[1,2]})))
    run=InvestigationEngine(ScriptedAdapter(handlers),tool_broker=broker).run("why")
    assert run.stage is Stage.AWAITING_OUTCOME
    assert calls["n"]==2
    assert any(e.event_type=="tools_executed" for e in run.events)
