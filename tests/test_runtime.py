from evidence_first.adapters.scripted import ScriptedAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.result import AgentDecision,AgentResult
from evidence_first.runtime import InvestigationEngine,Stage

ARTIFACT_BY_ROLE={
    AgentRole.EVIDENCE_INTAKE_COORDINATOR:"intake_manifest",
    AgentRole.INVESTIGATION_PLANNER:"investigation_plan",
    AgentRole.SIGNAL_VALIDATOR:"signal_validation_result",
    AgentRole.DATA_QUALITY_INVESTIGATOR:"data_quality_findings",
    AgentRole.HYPOTHESIS_GENERATOR:"hypotheses",
    AgentRole.EVIDENCE_ANALYST:"analysis_results",
    AgentRole.CONTRADICTION_INVESTIGATOR:"contradiction_findings",
    AgentRole.CONFOUND_REVIEWER:"confound_findings",
    AgentRole.CONTRIBUTION_ANALYST:"contribution_estimates",
    AgentRole.CRITIC:"critic_approved_conclusion",
    AgentRole.INTERVENTION_PLANNER:"validation_plan",
    AgentRole.OUTCOME_EVALUATOR:"outcome_assessment",
    AgentRole.MEMORY_CURATOR:"memory_entries",
}

def ok(spec,context):
    return AgentResult(spec.role,AgentDecision.CONTINUE,"ok",{ARTIFACT_BY_ROLE[spec.role]:{"ok":True}})

def test_engine_pauses_for_post_intervention_evidence():
    handlers={r:ok for r in AgentRole}
    run=InvestigationEngine(ScriptedAdapter(handlers)).run("why")
    assert run.stage is Stage.AWAITING_OUTCOME
    assert AgentRole.INTERVENTION_PLANNER in [r.role for r in run.results]
    assert AgentRole.OUTCOME_EVALUATOR not in [r.role for r in run.results]

def test_engine_completes_when_outcome_evidence_supplied():
    handlers={r:ok for r in AgentRole}
    run=InvestigationEngine(ScriptedAdapter(handlers)).run("why",{"post_intervention_evidence":{"metric":"recovered"}})
    assert run.stage is Stage.COMPLETE
    assert len(run.results)==len(AgentRole)

def test_engine_stops_on_blocking_agent():
    handlers={r:ok for r in AgentRole}
    def block(spec,ctx): return AgentResult(spec.role,AgentDecision.BLOCK,"bad signal")
    handlers[AgentRole.SIGNAL_VALIDATOR]=block
    run=InvestigationEngine(ScriptedAdapter(handlers)).run("why")
    assert run.stage is Stage.BLOCKED
    assert run.blocked_by=="signal_validator"
