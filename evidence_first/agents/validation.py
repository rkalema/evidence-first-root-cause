from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import AgentRole, AgentSpec, DecisionRight
from .result import AgentDecision, AgentResult


@dataclass(frozen=True)
class ContractViolation:
    code: str
    message: str


MANDATORY_OUTPUTS: dict[AgentRole, tuple[str, ...]] = {
    AgentRole.EVIDENCE_INTAKE_COORDINATOR: ("available_evidence_inventory",),
    AgentRole.INVESTIGATION_PLANNER: ("investigation_plan",),
    AgentRole.SIGNAL_VALIDATOR: ("validated_signal",),
    AgentRole.DATA_QUALITY_INVESTIGATOR: ("data_quality_findings",),
    AgentRole.HYPOTHESIS_GENERATOR: ("hypotheses",),
    AgentRole.EVIDENCE_ANALYST: ("segmentation_results",),
    AgentRole.CONTRADICTION_INVESTIGATOR: ("surviving_hypotheses",),
    AgentRole.CONFOUND_REVIEWER: ("confound_findings",),
    AgentRole.CONTRIBUTION_ANALYST: ("draft_conclusion",),
    AgentRole.CRITIC: ("critic_approved_conclusion",),
    AgentRole.INTERVENTION_PLANNER: ("validation_plan",),
    AgentRole.OUTCOME_EVALUATOR: ("outcome_assessment",),
    AgentRole.MEMORY_CURATOR: ("memory_entries",),
}


def validate_agent_result(
    spec: AgentSpec,
    result: AgentResult,
    *,
    require_outputs: bool = True,
) -> tuple[ContractViolation, ...]:
    problems: list[ContractViolation] = []

    if not isinstance(result, AgentResult):
        return (ContractViolation("wrong_type", "adapter did not return AgentResult"),)

    if result.role is not spec.role:
        problems.append(
            ContractViolation(
                "wrong_role",
                f"expected {spec.role.value}, got {getattr(result.role, 'value', result.role)!r}",
            )
        )

    if not isinstance(result.summary, str) or not result.summary.strip():
        problems.append(
            ContractViolation("invalid_summary", "agent result summary must be a non-empty string")
        )

    if not isinstance(result.artifacts, dict):
        problems.append(
            ContractViolation("invalid_artifacts", "agent artifacts must be an object/dict")
        )
        return tuple(problems)

    undeclared = sorted(set(result.artifacts) - set(spec.outputs))
    if undeclared:
        problems.append(
            ContractViolation(
                "undeclared_artifact",
                "undeclared artifact(s): " + ", ".join(undeclared),
            )
        )

    if require_outputs and result.decision is AgentDecision.CONTINUE:
        missing = [
            name
            for name in MANDATORY_OUTPUTS.get(spec.role, ())
            if name not in result.artifacts
        ]
        if missing:
            problems.append(
                ContractViolation(
                    "missing_required_output",
                    "missing required output(s): " + ", ".join(missing),
                )
            )

    if result.decision is AgentDecision.COMPLETE and (
        DecisionRight.APPROVE_FINAL_CONCLUSION not in spec.decision_rights
    ):
        problems.append(
            ContractViolation(
                "decision_right_violation",
                f"{spec.role.value} may not return COMPLETE",
            )
        )

    if not isinstance(result.evidence_ids, tuple) or not all(
        isinstance(item, str) and item.strip() for item in result.evidence_ids
    ):
        problems.append(
            ContractViolation(
                "invalid_evidence_ids",
                "evidence_ids must be a tuple of non-empty strings",
            )
        )

    if not isinstance(result.unknowns, tuple) or not all(
        isinstance(item, str) for item in result.unknowns
    ):
        problems.append(
            ContractViolation("invalid_unknowns", "unknowns must be a tuple of strings")
        )

    return tuple(problems)
