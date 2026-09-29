from evidence_first.adapters.scripted import ScriptedAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.result import AgentDecision, AgentResult
from evidence_first.runtime import InvestigationEngine, Stage
from tests.runtime_fixtures import secure_handlers


def test_engine_pauses_for_post_intervention_evidence():
    run = InvestigationEngine(ScriptedAdapter(secure_handlers())).run("why")
    assert run.stage is Stage.AWAITING_OUTCOME
    assert AgentRole.INTERVENTION_PLANNER in [r.role for r in run.results]
    assert AgentRole.OUTCOME_EVALUATOR not in [r.role for r in run.results]


def test_engine_completes_when_outcome_evidence_supplied():
    run = InvestigationEngine(ScriptedAdapter(secure_handlers())).run(
        "why",
        {"post_intervention_evidence": {"metric": "recovered"}},
    )
    assert run.stage is Stage.COMPLETE
    assert len(run.results) == len(AgentRole)


def test_engine_stops_on_blocking_agent():
    handlers = secure_handlers()

    def block(spec, ctx):
        return AgentResult(spec.role, AgentDecision.BLOCK, "bad signal")

    handlers[AgentRole.SIGNAL_VALIDATOR] = block
    run = InvestigationEngine(ScriptedAdapter(handlers)).run("why")
    assert run.stage is Stage.BLOCKED
    assert run.blocked_by == "signal_validator"
