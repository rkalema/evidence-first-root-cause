from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from evidence_first.adapters.base import AgentAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.catalog import default_agent_registry
from evidence_first.agents.orchestrator import InvestigationOrchestrator
from evidence_first.agents.result import AgentDecision, AgentResult
from evidence_first.runtime.events import InvestigationEvent

class Stage(str, Enum):
    PLANNING="planning"
    SIGNAL_VALIDATION="signal_validation"
    DATA_QUALITY="data_quality"
    HYPOTHESES="hypotheses"
    CONTRADICTION="contradiction"
    CONFOUND="confound"
    CONTRIBUTION="contribution"
    CRITIC="critic"
    INTERVENTION="intervention"
    COMPLETE="complete"
    BLOCKED="blocked"

ROLE_STAGE={
    AgentRole.INVESTIGATION_PLANNER: Stage.PLANNING,
    AgentRole.SIGNAL_VALIDATOR: Stage.SIGNAL_VALIDATION,
    AgentRole.DATA_QUALITY_INVESTIGATOR: Stage.DATA_QUALITY,
    AgentRole.HYPOTHESIS_GENERATOR: Stage.HYPOTHESES,
    AgentRole.CONTRADICTION_INVESTIGATOR: Stage.CONTRADICTION,
    AgentRole.CONFOUND_REVIEWER: Stage.CONFOUND,
    AgentRole.CONTRIBUTION_ANALYST: Stage.CONTRIBUTION,
    AgentRole.CRITIC: Stage.CRITIC,
    AgentRole.INTERVENTION_PLANNER: Stage.INTERVENTION,
}

@dataclass
class InvestigationRun:
    question: str
    context: dict[str, Any]=field(default_factory=dict)
    results: list[AgentResult]=field(default_factory=list)
    events: list[InvestigationEvent]=field(default_factory=list)
    stage: Stage=Stage.PLANNING
    blocked_by: str | None=None

    def artifact_context(self) -> dict[str, Any]:
        merged=dict(self.context)
        for result in self.results:
            merged.update(result.artifacts)
        return merged

class InvestigationEngine:
    def __init__(self, adapter: AgentAdapter):
        self.adapter=adapter
        self.registry=default_agent_registry()
        self.plan=InvestigationOrchestrator().build_plan()

    def run(self, question: str, context: dict[str, Any] | None=None) -> InvestigationRun:
        run=InvestigationRun(question=question, context=dict(context or {}))
        run.context.setdefault("problem_statement", question)
        for task in self.plan.tasks:
            spec=self.registry[task.role]
            run.stage=ROLE_STAGE[task.role]
            run.events.append(InvestigationEvent("agent_started",run.stage.value,spec.purpose,task.role.value))
            result=self.adapter.run(spec, run.artifact_context())
            run.results.append(result)
            for unknown in result.unknowns:
                run.context.setdefault("unknowns",[]).append(unknown)
            run.events.append(InvestigationEvent("agent_finished",run.stage.value,result.summary,task.role.value,{"decision":result.decision.value}))
            if result.decision is AgentDecision.BLOCK:
                run.stage=Stage.BLOCKED
                run.blocked_by=task.role.value
                run.events.append(InvestigationEvent("investigation_blocked",run.stage.value,result.summary,task.role.value))
                return run
            if result.decision is AgentDecision.REVISE and task.role is AgentRole.CRITIC:
                run.stage=Stage.BLOCKED
                run.blocked_by=task.role.value
                run.events.append(InvestigationEvent("critic_rejected",run.stage.value,result.summary,task.role.value))
                return run
        run.stage=Stage.COMPLETE
        run.events.append(InvestigationEvent("investigation_complete",run.stage.value,"Investigation completed governed sequence.","engine"))
        return run
