from __future__ import annotations

import json
from pathlib import Path

from scripts.evaluate_case import score


ROOT = Path(__file__).resolve().parents[1]


def load_case(name: str) -> dict:
    with (ROOT / "benchmarks" / "cases" / f"{name}.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def base_result(
    case: dict,
    status: str,
    leading: str,
    evidence_class: str = "conclusion",
    confidence: str = "medium",
) -> dict:
    required = case["expected"].get("required_terms", [])
    concept = required[0] if required else "temporal comparison"
    return {
        "case_id": case["id"],
        "status": status,
        "problem": {"statement": "x", "metric": "m", "baseline": "b", "observed": "o"},
        "signal_validation": {
            "trustworthy": True,
            "checks": [{"check": "freshness", "result": "ok"}],
            "notes": "validated",
        },
        "observations": [{"statement": "x", "evidence": "source record"}],
        "hypotheses": [
            {
                "hypothesis": "primary mechanism",
                "mechanism": f"Tests {concept} against the observed pattern.",
                "evidence_for": [f"{concept} supports the primary explanation."],
                "evidence_against": ["No decisive contradiction remains."],
                "result": "supported",
            },
            {
                "hypothesis": "alternative mechanism",
                "mechanism": "A different mechanism that predicts a different pattern.",
                "evidence_for": ["A plausible alternative exists."],
                "evidence_against": ["Comparison evidence contradicts this alternative."],
                "result": "not_supported",
            },
            {
                "hypothesis": "measurement explanation",
                "mechanism": "A measurement or denominator artifact.",
                "evidence_for": [],
                "evidence_against": ["The measured signal passed validation."],
                "result": "not_supported",
            },
        ],
        "leading_explanation": {"statement": leading, "evidence_class": evidence_class},
        "confidence": {"level": confidence, "rationale": "evidence"},
        "impact": {"summary": "impact"},
        "unknowns": [],
        "recommended_actions": {
            "containment": [],
            "corrective": [],
            "preventive": [],
            "investigation": [],
        },
        "validation_plan": {
            "target_metric": "m",
            "review_timing": "7 days",
            "comparison_method": "before/after with reference",
            "success_criteria": "return to baseline",
        },
    }


def test_strong_case_passes() -> None:
    case = load_case("contradictory-supplier")
    result = base_result(
        case,
        "root_cause_supported",
        "A shared calibration change is the strongest explanation; three unaffected Supplier B plants contradict the supplier claim.",
        confidence="high",
    )
    report = score(case, result)
    assert report["passed"]
    assert report["score"] >= 90


def test_forbidden_causal_story_is_penalized() -> None:
    case = load_case("contradictory-supplier")
    result = base_result(
        case,
        "root_cause_supported",
        "Supplier B caused the increase despite the calibration change and three unaffected plants.",
        confidence="high",
    )
    report = score(case, result)
    assert report["score"] < 100


def test_data_quality_case_requires_untrusted_signal() -> None:
    case = load_case("data-quality-denominator")
    result = base_result(
        case,
        "data_quality_blocked",
        "Admissions denominator is incomplete, so clinical root-cause analysis is blocked.",
        evidence_class="unknown",
        confidence="low",
    )
    result["signal_validation"]["trustworthy"] = False
    result["hypotheses"] = result["hypotheses"][:1]
    result["hypotheses"][0]["result"] = "untested"
    result["observations"][0]["statement"] = "The admissions denominator contains only 51% of expected records."
    report = score(case, result)
    assert report["passed"]
