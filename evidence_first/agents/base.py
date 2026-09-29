from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AgentRole(str, Enum):
    EVIDENCE_INTAKE_COORDINATOR = "evidence_intake_coordinator"
    INVESTIGATION_PLANNER = "investigation_planner"
    SIGNAL_VALIDATOR = "signal_validator"
    DATA_QUALITY_INVESTIGATOR = "data_quality_investigator"
    HYPOTHESIS_GENERATOR = "hypothesis_generator"
    EVIDENCE_ANALYST = "evidence_analyst"
    CONTRADICTION_INVESTIGATOR = "contradiction_investigator"
    CONFOUND_REVIEWER = "confound_reviewer"
    CONTRIBUTION_ANALYST = "contribution_analyst"
    CRITIC = "critic"
    INTERVENTION_PLANNER = "intervention_planner"
    OUTCOME_EVALUATOR = "outcome_evaluator"
    MEMORY_CURATOR = "memory_curator"


class DecisionRight(str, Enum):
    READ_EVIDENCE = "read_evidence"
    ADD_EVIDENCE = "add_evidence"
    ADD_HYPOTHESIS = "add_hypothesis"
    RUN_ANALYTICAL_TOOL = "run_analytical_tool"
    CHALLENGE_HYPOTHESIS = "challenge_hypothesis"
    CLASSIFY_CONFOUND = "classify_confound"
    QUANTIFY_CONTRIBUTION = "quantify_contribution"
    BLOCK_CAUSAL_ANALYSIS = "block_causal_analysis"
    RECOMMEND_ACTION = "recommend_action"
    EVALUATE_OUTCOME = "evaluate_outcome"
    WRITE_MEMORY = "write_memory"
    APPROVE_FINAL_CONCLUSION = "approve_final_conclusion"


@dataclass(frozen=True)
class AgentSpec:
    role: AgentRole
    purpose: str
    required_inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    decision_rights: tuple[DecisionRight, ...]
    stop_conditions: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.purpose.strip():
            raise ValueError("agent purpose cannot be empty")
        if not self.required_inputs:
            raise ValueError("required inputs missing")
        if not self.outputs:
            raise ValueError("outputs missing")
        if not self.acceptance_criteria:
            raise ValueError("acceptance criteria missing")


@dataclass(frozen=True)
class AgentTask:
    role: AgentRole
    objective: str
    required_artifacts: tuple[str, ...] = ()
    blocking: bool = True
    metadata: dict[str, str] = field(default_factory=dict)
