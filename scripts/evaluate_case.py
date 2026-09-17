"""Deterministic behavioral benchmark scoring for Evidence-First Root Cause."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Criterion:
    name: str
    passed: bool
    points: int
    detail: str


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, list):
        return " ".join(_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_text(item) for item in value.values())
    return str(value).lower()


def score(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    criteria: list[Criterion] = []

    def add(name: str, passed: bool, points: int, detail: str) -> None:
        criteria.append(Criterion(name, passed, points, detail))

    actual_status = result.get("status")
    expected_status = expected["status"]
    add("status", actual_status == expected_status, 25, f"expected {expected_status!r}, got {actual_status!r}")

    signal = result.get("signal_validation", {})
    if "signal_trustworthy" in expected:
        actual = signal.get("trustworthy")
        target = expected["signal_trustworthy"]
        add("signal_validation", actual is target, 15, f"expected trustworthy={target}, got {actual!r}")

    hypotheses = result.get("hypotheses", [])
    minimum = expected.get("min_hypotheses", 2)
    add("competing_hypotheses", len(hypotheses) >= minimum, 15, f"expected at least {minimum} hypotheses, got {len(hypotheses)}")

    all_text = _text(result)
    required_terms = expected.get("required_terms", [])
    missing = [term for term in required_terms if term.lower() not in all_text]
    add("required_evidence", not missing, 15, "missing required evidence terms: " + ", ".join(missing) if missing else "all required evidence surfaced")

    forbidden_terms = expected.get("forbidden_terms", [])
    leading_text = _text(result.get("leading_explanation", {}))
    present = [term for term in forbidden_terms if term.lower() in leading_text]
    add("avoids_forbidden_conclusion", not present, 10, "forbidden conclusion terms present: " + ", ".join(present) if present else "no prohibited conclusion detected")

    leading_class = result.get("leading_explanation", {}).get("evidence_class")
    allowed_classes = expected.get("allowed_evidence_classes", ["conclusion", "inference", "unknown"])
    add("evidence_class", leading_class in allowed_classes, 5, f"allowed {allowed_classes}, got {leading_class!r}")

    confidence = result.get("confidence", {}).get("level")
    allowed_confidence = expected.get("allowed_confidence", ["low", "medium", "high"])
    add("confidence_calibration", confidence in allowed_confidence, 5, f"allowed {allowed_confidence}, got {confidence!r}")

    validation = result.get("validation_plan", {})
    has_plan = all(bool(validation.get(field)) for field in ("target_metric", "review_timing", "comparison_method", "success_criteria"))
    add("intervention_validation", has_plan, 10, "validation plan complete" if has_plan else "validation plan incomplete")

    earned = sum(item.points for item in criteria if item.passed)
    possible = sum(item.points for item in criteria)
    pct = round(100 * earned / possible, 1) if possible else 0.0

    return {
        "case_id": case.get("id"),
        "score": pct,
        "earned_points": earned,
        "possible_points": possible,
        "passed": pct >= expected.get("pass_score", 85),
        "criteria": [asdict(item) for item in criteria],
    }
