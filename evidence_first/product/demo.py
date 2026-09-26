from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd

from evidence_first.adapters.scripted import ScriptedAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.result import AgentDecision, AgentResult
from evidence_first.product.progress import ProgressAdapter
from evidence_first.product.sources import prepare_sources
from evidence_first.product.workspace import create_run_workspace, write_run_artifacts
from evidence_first.runtime import InvestigationEngine, Stage


DEMO_CSV = """depot,period,labor_hours,order_volume,sla,release_to_ready_minutes
A,before,100,1000,91,46
A,after,87,1240,61,91
B,before,100,980,92,44
B,after,100,1215,86,55
C,before,100,1010,90,47
C,after,86,1250,63,88
"""


class DemoAdapter:
    """Deterministic demonstration of the governed lifecycle."""

    def __init__(self):
        self.analysis_rounds = 0

    def run(self, spec, context):
        role = spec.role

        if role is AgentRole.EVIDENCE_INTAKE_COORDINATOR:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "Evidence sources were fingerprinted and accepted.",
                {
                    "available_evidence_inventory": context.get(
                        "source_inventory", ()
                    ),
                    "intake_manifest": {"accepted": True},
                },
            )

        if role is AgentRole.INVESTIGATION_PLANNER:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "Plan: validate the SLA signal, test capacity and demand explanations, then challenge the leader.",
                {
                    "investigation_plan": {
                        "steps": [
                            "validate signal",
                            "compare depots and periods",
                            "test labor and demand hypotheses",
                            "seek contradictory evidence",
                        ]
                    }
                },
            )

        if role is AgentRole.SIGNAL_VALIDATOR:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "The SLA decline is present in the supplied records and can be investigated.",
                {
                    "validated_signal": {"trustworthy": True},
                    "signal_validation_result": {"trustworthy": True},
                },
            )

        if role is AgentRole.DATA_QUALITY_INVESTIGATOR:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "No blocking source defect was found; the small demo remains illustrative rather than causal proof.",
                {
                    "data_quality_findings": {
                        "blocking": False,
                        "limitations": ["small synthetic sample"],
                    }
                },
            )

        if role is AgentRole.HYPOTHESIS_GENERATOR:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "Generated labor-capacity and demand-volume alternatives.",
                {
                    "hypotheses": [
                        {
                            "hypothesis_id": "h1",
                            "hypothesis": "Reduced labor capacity drove the SLA decline.",
                            "mechanism": "Lower available labor increases release-to-ready time.",
                            "relationship": "competing",
                        },
                        {
                            "hypothesis_id": "h2",
                            "hypothesis": "Demand growth alone drove the SLA decline.",
                            "mechanism": "Higher order volume overwhelms unchanged capacity.",
                            "relationship": "competing",
                        },
                    ]
                },
            )

        if role is AgentRole.EVIDENCE_ANALYST:
            self.analysis_rounds += 1
            outcomes = context.get("tool_outcomes", ())
            if not outcomes:
                return AgentResult(
                    role,
                    AgentDecision.CONTINUE,
                    "Requesting depot-period SLA and release-to-ready comparisons.",
                    {
                        "tool_requests": [
                            {
                                "name": "dataframe.group_metric",
                                "arguments": {
                                    "source_id": "delivery_incident.csv",
                                    "group": "period",
                                    "metric": "sla",
                                    "agg": "mean",
                                },
                            },
                            {
                                "name": "dataframe.group_metric",
                                "arguments": {
                                    "source_id": "delivery_incident.csv",
                                    "group": "period",
                                    "metric": "release_to_ready_minutes",
                                    "agg": "mean",
                                },
                            },
                        ]
                    },
                )

            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "The after period has materially lower SLA and longer release-to-ready time; labor-short depots show the largest deterioration.",
                {
                    "segmentation_results": {
                        "tool_outcomes": outcomes,
                    },
                    "analysis_results": {"tool_outcomes": outcomes},
                    "derived_evidence": [
                        {
                            "evidence_id": "demo:e1",
                            "statement": "SLA is materially lower in the after period while release-to-ready time is materially higher.",
                            "kind": "observation",
                            "source": "demo-analysis",
                            "reliability": 1.0,
                        },
                        {
                            "evidence_id": "demo:e2",
                            "statement": "Depot B retained full labor and experienced a smaller SLA decline than labor-short depots A and C.",
                            "kind": "observation",
                            "source": "demo-analysis",
                            "reliability": 1.0,
                        },
                        {
                            "evidence_id": "demo:e3",
                            "statement": "Order volume increased across all depots, including the depot with the smaller SLA decline.",
                            "kind": "observation",
                            "source": "demo-analysis",
                            "reliability": 1.0,
                        },
                    ],
                    "hypothesis_tests": [
                        {
                            "hypothesis_id": "h1",
                            "evidence_for": ["demo:e1", "demo:e2"],
                            "evidence_against": [],
                        },
                        {
                            "hypothesis_id": "h2",
                            "evidence_for": ["demo:e3"],
                            "evidence_against": ["demo:e2"],
                        },
                    ],
                    "tool_requests": [],
                    "method_limits": ["synthetic example; no randomized intervention"],
                },
            )

        if role is AgentRole.CONTRADICTION_INVESTIGATOR:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "Demand rose everywhere, but the depot without labor loss deteriorated less; labor capacity survives the contradiction search.",
                {
                    "surviving_hypotheses": ["h1"],
                    "contradiction_findings": {
                        "h2": "The comparison depot weakens demand-alone as a sufficient explanation."
                    },
                },
            )

        if role is AgentRole.CONFOUND_REVIEWER:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "Order-volume growth is a plausible concurrent contributor, but it does not explain the cross-depot difference by itself.",
                {
                    "confound_findings": {
                        "unresolved_material_confounds": 0,
                        "noted": ["order volume increased across depots"],
                    }
                },
            )

        if role is AgentRole.CONTRIBUTION_ANALYST:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "The demo supports labor capacity as the leading mechanism; exact contribution percentages are not identified.",
                {
                    "draft_conclusion": {
                        "statement": "Reduced labor capacity is the strongest supported explanation for the larger SLA deterioration.",
                        "evidence_ids": ["demo:e1", "demo:e2"],
                    },
                    "precision_limits": [
                        "The demo does not support exact causal contribution percentages."
                    ],
                },
            )

        if role is AgentRole.CRITIC:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "Approved with observational limitations: the leading explanation survives the supplied comparison evidence.",
                {
                    "critic_approved_conclusion": {
                        "statement": "Reduced labor capacity is the strongest supported explanation for the larger SLA deterioration.",
                        "evidence_ids": ["demo:e1", "demo:e2"],
                    },
                    "critic_verdict": "approved",
                },
                evidence_ids=("demo:e1", "demo:e2"),
            )

        if role is AgentRole.INTERVENTION_PLANNER:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "Restore labor coverage in one affected depot and compare SLA and release-to-ready recovery against the reference depot.",
                {
                    "validation_plan": {
                        "target_metric": "sla",
                        "baseline": "pre-incident depot SLA",
                        "comparison": "affected depot before/after with depot B as reference",
                        "timing": "7 operating days",
                        "success_criteria": "SLA and release-to-ready move materially toward baseline after labor restoration",
                    },
                    "containment": ["restore short-term pick/pack coverage"],
                    "corrective_action": ["align staffing to sustained order volume"],
                    "preventive_action": ["alert on labor-to-volume capacity gap"],
                },
            )

        if role is AgentRole.OUTCOME_EVALUATOR:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "Synthetic post-intervention evidence is consistent with the predicted recovery.",
                {
                    "outcome_assessment": {
                        "result": "prediction_consistent",
                        "note": "Demo outcome supplied for lifecycle illustration only.",
                    }
                },
            )

        if role is AgentRole.MEMORY_CURATOR:
            return AgentResult(
                role,
                AgentDecision.CONTINUE,
                "Stored the demo lesson as context, not new evidence.",
                {
                    "memory_entries": [
                        {
                            "hypothesis": "labor-capacity constraint",
                            "outcome": "prediction_consistent",
                            "evidence_ids": ["demo:e1", "demo:e2"],
                        }
                    ]
                },
            )

        raise RuntimeError(f"unhandled demo role: {role.value}")


def run_demo(
    *,
    out_dir: Path,
    stream,
) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    data_path = out_dir / "delivery_incident.csv"
    data_path.write_text(DEMO_CSV, encoding="utf-8")

    prepared = prepare_sources([data_path])
    adapter = ProgressAdapter(DemoAdapter(), stream=stream)
    engine = InvestigationEngine(
        adapter,
        tool_broker=prepared.tool_broker,
    )
    question = "Why did same-day delivery SLA deteriorate in the affected depots?"
    run = engine.run(
        question,
        {
            "source_inventory": prepared.source_inventory,
            "evidence_records": prepared.evidence_records,
            "domain": "operations",
            "post_intervention_evidence": {
                "affected_depot_sla": "recovered toward baseline",
                "release_to_ready": "improved",
            },
        },
    )
    if run.stage is not Stage.COMPLETE:
        raise RuntimeError(f"bundled demo did not complete: {run.stage.value}")

    workspace = create_run_workspace(out_dir / "runs", question)
    return write_run_artifacts(
        run,
        workspace,
        provider="demo",
        model="deterministic-demo",
        domain="operations",
        source_inventory=prepared.source_inventory,
    )
