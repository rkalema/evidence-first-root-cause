from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from evidence_first.adapters.base import AgentAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.catalog import default_agent_registry
from evidence_first.agents.orchestrator import InvestigationOrchestrator
from evidence_first.agents.result import AgentDecision, AgentResult
from evidence_first.agents.validation import validate_agent_result
from evidence_first.runtime.events import InvestigationEvent
from evidence_first.runtime.tool_broker import ToolExecutionBroker, ToolRequest


class Stage(str, Enum):
    INTAKE = "intake"
    PLANNING = "planning"
    SIGNAL_VALIDATION = "signal_validation"
    DATA_QUALITY = "data_quality"
    HYPOTHESES = "hypotheses"
    CONTRADICTION = "contradiction"
    CONFOUND = "confound"
    CONTRIBUTION = "contribution"
    CRITIC = "critic"
    INTERVENTION = "intervention"
    OUTCOME = "outcome"
    MEMORY = "memory"
    AWAITING_OUTCOME = "awaiting_outcome"
    COMPLETE = "complete"
    BLOCKED = "blocked"


ROLE_STAGE = {
    AgentRole.EVIDENCE_INTAKE_COORDINATOR: Stage.INTAKE,
    AgentRole.INVESTIGATION_PLANNER: Stage.PLANNING,
    AgentRole.SIGNAL_VALIDATOR: Stage.SIGNAL_VALIDATION,
    AgentRole.DATA_QUALITY_INVESTIGATOR: Stage.DATA_QUALITY,
    AgentRole.HYPOTHESIS_GENERATOR: Stage.HYPOTHESES,
    AgentRole.EVIDENCE_ANALYST: Stage.HYPOTHESES,
    AgentRole.CONTRADICTION_INVESTIGATOR: Stage.CONTRADICTION,
    AgentRole.CONFOUND_REVIEWER: Stage.CONFOUND,
    AgentRole.CONTRIBUTION_ANALYST: Stage.CONTRIBUTION,
    AgentRole.CRITIC: Stage.CRITIC,
    AgentRole.INTERVENTION_PLANNER: Stage.INTERVENTION,
    AgentRole.OUTCOME_EVALUATOR: Stage.OUTCOME,
    AgentRole.MEMORY_CURATOR: Stage.MEMORY,
}


@dataclass
class InvestigationRun:
    question: str
    context: dict[str, Any] = field(default_factory=dict)
    results: list[AgentResult] = field(default_factory=list)
    events: list[InvestigationEvent] = field(default_factory=list)
    stage: Stage = Stage.PLANNING
    blocked_by: str | None = None

    def artifact_context(self) -> dict[str, Any]:
        merged = dict(self.context)
        for result in self.results:
            merged.update(result.artifacts)
        return merged


class InvestigationEngine:
    def __init__(
        self,
        adapter: AgentAdapter,
        tool_broker: ToolExecutionBroker | None = None,
        max_tool_rounds: int = 3,
    ):
        self.adapter = adapter
        self.tool_broker = tool_broker
        self.max_tool_rounds = max_tool_rounds
        self.registry = default_agent_registry()
        self.plan = InvestigationOrchestrator().build_plan()

    def run(
        self,
        question: str,
        context: dict[str, Any] | None = None,
    ) -> InvestigationRun:
        run = InvestigationRun(question=question, context=dict(context or {}))
        run.context.setdefault("problem_statement", question)

        for task in self.plan.tasks:
            if (
                task.role is AgentRole.OUTCOME_EVALUATOR
                and "post_intervention_evidence" not in run.artifact_context()
            ):
                run.stage = Stage.AWAITING_OUTCOME
                run.events.append(
                    InvestigationEvent(
                        "awaiting_outcome",
                        run.stage.value,
                        "Intervention plan complete; post-intervention evidence is required.",
                        "engine",
                    )
                )
                return run

            spec = self.registry[task.role]
            run.stage = ROLE_STAGE[task.role]
            run.events.append(
                InvestigationEvent(
                    "agent_started",
                    run.stage.value,
                    spec.purpose,
                    task.role.value,
                )
            )

            result = self.adapter.run(spec, run.artifact_context())

            if task.role is AgentRole.EVIDENCE_ANALYST:
                for _ in range(self.max_tool_rounds):
                    requests = result.artifacts.get("tool_requests", [])
                    if not requests:
                        break
                    if self.tool_broker is None:
                        run.stage = Stage.BLOCKED
                        run.blocked_by = task.role.value
                        run.events.append(
                            InvestigationEvent(
                                "tooling_unavailable",
                                run.stage.value,
                                "Evidence Analyst requested tools but no tool broker is configured.",
                                task.role.value,
                            )
                        )
                        return run

                    parsed = [
                        ToolRequest(
                            str(item["name"]),
                            dict(item.get("arguments", {})),
                            tuple(item.get("source_ids", ())),
                        )
                        for item in requests
                    ]
                    outcomes = self.tool_broker.execute_many(parsed)
                    run.context.setdefault("tool_outcomes", []).extend(
                        [
                            {
                                "name": outcome.name,
                                "ok": outcome.ok,
                                "value": outcome.value,
                                "error": outcome.error,
                                "source_ids": outcome.source_ids,
                            }
                            for outcome in outcomes
                        ]
                    )
                    run.events.append(
                        InvestigationEvent(
                            "tools_executed",
                            run.stage.value,
                            f"{len(outcomes)} tool request(s) executed.",
                            task.role.value,
                        )
                    )
                    result = self.adapter.run(spec, run.artifact_context())

            violations = validate_agent_result(spec, result)
            if violations:
                run.stage = Stage.BLOCKED
                run.blocked_by = task.role.value
                message = "; ".join(v.message for v in violations)
                run.events.append(
                    InvestigationEvent(
                        "contract_violation",
                        run.stage.value,
                        message,
                        task.role.value,
                    )
                )
                return run

            run.results.append(result)
            for unknown in result.unknowns:
                run.context.setdefault("unknowns", []).append(unknown)

            run.events.append(
                InvestigationEvent(
                    "agent_finished",
                    run.stage.value,
                    result.summary,
                    task.role.value,
                    {"decision": result.decision.value},
                )
            )

            if result.decision is AgentDecision.BLOCK:
                run.stage = Stage.BLOCKED
                run.blocked_by = task.role.value
                run.events.append(
                    InvestigationEvent(
                        "investigation_blocked",
                        run.stage.value,
                        result.summary,
                        task.role.value,
                    )
                )
                return run

            if result.decision is AgentDecision.REVISE and task.role is AgentRole.CRITIC:
                run.stage = Stage.BLOCKED
                run.blocked_by = task.role.value
                run.events.append(
                    InvestigationEvent(
                        "critic_rejected",
                        run.stage.value,
                        result.summary,
                        task.role.value,
                    )
                )
                return run

        run.stage = Stage.COMPLETE
        run.events.append(
            InvestigationEvent(
                "investigation_complete",
                run.stage.value,
                "Investigation completed governed sequence.",
                "engine",
            )
        )
        return run
