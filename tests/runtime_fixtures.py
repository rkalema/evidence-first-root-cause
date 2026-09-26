from __future__ import annotations

from evidence_first.agents.base import AgentRole
from evidence_first.agents.result import AgentDecision, AgentResult


def secure_handler(spec, context):
    role = spec.role
    if role is AgentRole.EVIDENCE_INTAKE_COORDINATOR:
        artifacts = {"available_evidence_inventory": []}
    elif role is AgentRole.INVESTIGATION_PLANNER:
        artifacts = {"investigation_plan": {"steps": ["validate", "test alternatives"]}}
    elif role is AgentRole.SIGNAL_VALIDATOR:
        artifacts = {
            "signal_validation_result": {"trustworthy": True},
            "validated_signal": {"trustworthy": True},
        }
    elif role is AgentRole.DATA_QUALITY_INVESTIGATOR:
        artifacts = {"data_quality_findings": {"blocking": False}}
    elif role is AgentRole.HYPOTHESIS_GENERATOR:
        artifacts = {
            "hypotheses": [
                {
                    "hypothesis_id": "h1",
                    "hypothesis": "Primary mechanism",
                    "mechanism": "Mechanism A",
                    "relationship": "competing",
                },
                {
                    "hypothesis_id": "h2",
                    "hypothesis": "Alternative mechanism",
                    "mechanism": "Mechanism B",
                    "relationship": "competing",
                },
            ]
        }
    elif role is AgentRole.EVIDENCE_ANALYST:
        artifacts = {
            "segmentation_results": {},
            "analysis_results": {},
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
                    "statement": "Alternative mechanism is contradicted by the comparison group.",
                    "kind": "observation",
                    "source": "test",
                    "reliability": 1.0,
                },
            ],
            "hypothesis_tests": [
                {"hypothesis_id": "h1", "evidence_for": ["e1"], "evidence_against": []},
                {"hypothesis_id": "h2", "evidence_for": [], "evidence_against": ["e2"]},
            ],
            "tool_requests": [],
        }
    elif role is AgentRole.CONTRADICTION_INVESTIGATOR:
        artifacts = {
            "surviving_hypotheses": ["h1"],
            "contradiction_findings": {"h2": "contradicted"},
        }
    elif role is AgentRole.CONFOUND_REVIEWER:
        artifacts = {"confound_findings": {"unresolved_material_confounds": 0}}
    elif role is AgentRole.CONTRIBUTION_ANALYST:
        artifacts = {"draft_conclusion": {"statement": "Primary mechanism is best supported."}}
    elif role is AgentRole.CRITIC:
        artifacts = {
            "critic_approved_conclusion": {
                "statement": "Primary mechanism is best supported.",
                "evidence_ids": ["e1"],
            },
            "critic_verdict": "approved",
        }
        return AgentResult(
            role,
            AgentDecision.CONTINUE,
            "approved",
            artifacts,
            evidence_ids=("e1",),
        )
    elif role is AgentRole.INTERVENTION_PLANNER:
        artifacts = {
            "validation_plan": {
                "target_metric": "sla",
                "baseline": 0.90,
                "comparison": "before/after",
                "timing": "7 days",
                "success_criteria": "sla >= 0.90",
            }
        }
    elif role is AgentRole.OUTCOME_EVALUATOR:
        artifacts = {"outcome_assessment": {"result": "evaluated"}}
    elif role is AgentRole.MEMORY_CURATOR:
        artifacts = {"memory_entries": []}
    else:
        artifacts = {spec.outputs[0]: {}}
    return AgentResult(role, AgentDecision.CONTINUE, "ok", artifacts)


def secure_handlers():
    return {role: secure_handler for role in AgentRole}
