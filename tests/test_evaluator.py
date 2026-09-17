from __future__ import annotations

import json
from pathlib import Path

from scripts.evaluate_case import score


ROOT = Path(__file__).resolve().parents[1]


def load_case(name: str) -> dict:
    with (ROOT / "benchmarks" / "cases" / f"{name}.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def base_result(status: str, leading: str, evidence_class: str = "conclusion", confidence: str = "medium") -> dict:
    return {
        "status": status,
        "problem": {"statement": "x", "metric": "m", "baseline": "b", "observed": "o"},
        "signal_validation": {"trustworthy": True, "checks": [{"check": "freshness", "result": "ok"}], "notes": "validated"},
        "observations": [{"statement": "x", "evidence": "source record"}],
        "hypotheses": [
            {"hypothesis": "h1", "mechanism": "m1", "evidence_for": [], "evidence_against": [], "result": "supported"},
            {"hypothesis": "h2", "mechanism": "m2", "evidence_for": [], "evidence_against": [], "result": "not_supported"},
            {"hypothesis": "h3", "mechanism": "m3", "evidence_for": [], "evidence_against": [], "result": "not_supported"}
        ],
        "leading_explanation": {"statement": leading, "evidence_class": evidence_class},
        "confidence": {"level": confidence, "rationale": "evidence"},
        "impact": {"summary": "impact"},
        "unknowns": [],
        "recommended_actions": {"containment": [], "corrective": [], "preventive": [], "investigation": []},
        "validation_plan": {
            "target_metric": "m",
            "review_timing": "7 days",
            "comparison_method": "before/after with reference",
            "success_criteria": "return to baseline"
        }
    }


def test_strong_case_passes() -> None:
    case = load_case("contradictory-supplier")
    result = base_result(
        "root_cause_supported",
        "A shared calibration change is the strongest explanation; three unaffected Supplier B plants contradict the supplier claim."
    )
    report = score(case, result)
    assert report["passed"]
    assert report["score"] >= 90


def test_forbidden_causal_story_is_penalized() -> None:
    case = load_case("contradictory-supplier")
    result = base_result(
        "root_cause_supported",
        "Supplier B caused the increase despite the calibration change and three unaffected plants."
    )
    report = score(case, result)
    assert report["score"] < 100


def test_data_quality_case_requires_untrusted_signal() -> None:
    case = load_case("data-quality-denominator")
    result = base_result(
        "data_quality_blocked",
        "Admissions denominator is incomplete, so clinical root-cause analysis is blocked.",
        evidence_class="unknown",
        confidence="low"
    )
    result["signal_validation"]["trustworthy"] = False
    result["hypotheses"] = result["hypotheses"][:1]
    result["observations"][0]["statement"] = "The admissions denominator contains only 51% of expected records."
    report = score(case, result)
    assert report["passed"]
