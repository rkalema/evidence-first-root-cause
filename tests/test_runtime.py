from evidence_first.adapters.scripted import ScriptedAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.result import AgentDecision,AgentResult
from evidence_first.runtime import InvestigationEngine,Stage

def ok(spec,context):
    key={
        AgentRole.INVESTIGATION_PLANNER:"investigation_plan",
        AgentRole.SIGNAL_VALIDATOR:"signal_validation_result",
        AgentRole.DATA_QUALITY_INVESTIGATOR:"data_quality_findings",
        AgentRole.HYPOTHESIS_GENERATOR:"hypotheses",
        AgentRole.CONTRADICTION_INVESTIGATOR:"contradiction_findings",
        AgentRole.CONFOUND_REVIEWER:"confound_findings",
        AgentRole.CONTRIBUTION_ANALYST:"contribution_estimates",
        AgentRole.CRITIC:"critic_verdict",
        AgentRole.INTERVENTION_PLANNER:"validation_plan",
    }[spec.role]
    return AgentResult(spec.role,AgentDecision.CONTINUE,"ok",{key:{"ok":True}})

def test_engine_runs_all_agents():
    handlers={r:ok for r in AgentRole}
    run=InvestigationEngine(ScriptedAdapter(handlers)).run("why")
    assert run.stage is Stage.COMPLETE
    assert len(run.results)==len(AgentRole)

def test_engine_stops_on_blocking_agent():
    handlers={r:ok for r in AgentRole}
    def block(spec,ctx): return AgentResult(spec.role,AgentDecision.BLOCK,"bad signal")
    handlers[AgentRole.SIGNAL_VALIDATOR]=block
    run=InvestigationEngine(ScriptedAdapter(handlers)).run("why")
    assert run.stage is Stage.BLOCKED
    assert run.blocked_by=="signal_validator"
