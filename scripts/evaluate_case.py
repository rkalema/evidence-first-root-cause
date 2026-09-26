"""Deterministic structural benchmark scoring for Evidence-First Root Cause."""

from __future__ import annotations

import re
import unicodedata
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
        return value
    if isinstance(value, list):
        return " ".join(_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_text(item) for item in value.values())
    return str(value)


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _conclusion_text(result: dict[str, Any]) -> str:
    fields = [
        result.get("leading_explanation", {}).get("statement", ""),
        result.get("impact", {}).get("summary", ""),
        result.get("recommended_actions", {}),
    ]
    return _norm(_text(fields))


def _negated(text: str, phrase: str) -> bool:
    pos = text.find(phrase)
    if pos < 0:
        return False
    window = text[max(0, pos - 90): pos + len(phrase) + 40]
    negators = (
        "does not support",
        "do not support",
        "not support",
        "no evidence",
        "not caused",
        "did not cause",
        "cannot conclude",
        "unsupported",
        "reject",
        "ruled out",
        "not responsible",
    )
    return any(token in window for token in negators)


def _forbidden_present(result: dict[str, Any], forbidden: list[str]) -> list[str]:
    text = _conclusion_text(result)
    hits: list[str] = []
    for raw in forbidden:
        phrase = _norm(raw)
        variants = {phrase}
        if " caused" in phrase:
            variants.add(phrase.replace(" caused", " was responsible for"))
            variants.add(phrase.replace(" caused", " drove"))
            variants.add(phrase.replace(" caused", " produced"))
        found = False
        for variant in variants:
            if variant in text and not _negated(text, variant):
                found = True
                break
        if found:
            hits.append(raw)
    return hits


def _hypothesis_reasoning_text(result: dict[str, Any]) -> str:
    parts: list[str] = []
    for hypothesis in result.get("hypotheses", []):
        if not isinstance(hypothesis, dict):
            continue
        parts.extend(hypothesis.get("evidence_for", []))
        parts.extend(hypothesis.get("evidence_against", []))
        parts.append(hypothesis.get("mechanism", ""))
        parts.append(hypothesis.get("hypothesis", ""))
    parts.append(result.get("leading_explanation", {}).get("statement", ""))
    return _norm(" ".join(map(str, parts)))


def _structural_hypotheses(result: dict[str, Any], status: str) -> tuple[bool, str]:
    hypotheses = [h for h in result.get("hypotheses", []) if isinstance(h, dict)]
    supported = [h for h in hypotheses if h.get("result") == "supported"]
    rejected = [h for h in hypotheses if h.get("result") == "not_supported"]
    partial = [h for h in hypotheses if h.get("result") == "partially_supported"]

    mechanisms = {_norm(str(h.get("mechanism", ""))) for h in hypotheses if h.get("mechanism")}
    evidence_shapes = {
        (
            tuple(map(_norm, map(str, h.get("evidence_for", [])))),
            tuple(map(_norm, map(str, h.get("evidence_against", [])))),
        )
        for h in hypotheses
    }
    diverse = len(mechanisms) >= 2 and len(evidence_shapes) >= 2

    if status == "root_cause_supported":
        ok = len(supported) >= 1 and len(rejected) >= 1 and diverse
    elif status == "multiple_contributors_supported":
        ok = len(supported) >= 2 and diverse
    elif status == "insufficient_evidence":
        ok = len(hypotheses) >= 2 and (len(partial) >= 1 or len(supported) == 0) and diverse
    elif status == "data_quality_blocked":
        ok = len(hypotheses) >= 1
    else:
        ok = False
    return ok, (
        f"supported={len(supported)}, rejected={len(rejected)}, "
        f"partial={len(partial)}, diverse={diverse}"
    )


def score(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    criteria: list[Criterion] = []

    def add(name: str, passed: bool, points: int, detail: str) -> None:
        criteria.append(Criterion(name, passed, points, detail))

    case_id = result.get("case_id")
    binding_ok = case_id == case.get("id")
    add(
        "case_binding",
        binding_ok,
        20,
        f"expected case_id={case.get('id')!r}, got {case_id!r}",
    )

    actual_status = result.get("status")
    expected_status = expected["status"]
    add("status", actual_status == expected_status, 20, f"expected {expected_status!r}, got {actual_status!r}")

    signal = result.get("signal_validation", {})
    actual_signal = signal.get("trustworthy")
    target_signal = expected.get("signal_trustworthy")
    add(
        "signal_validation",
        actual_signal is target_signal,
        10,
        f"expected trustworthy={target_signal}, got {actual_signal!r}",
    )

    hypotheses = result.get("hypotheses", [])
    minimum = expected.get("min_hypotheses", 2)
    add(
        "competing_hypotheses",
        len(hypotheses) >= minimum,
        10,
        f"expected at least {minimum}, got {len(hypotheses)}",
    )

    structure_ok, structure_detail = _structural_hypotheses(result, actual_status)
    add("hypothesis_structure", structure_ok, 15, structure_detail)

    reasoning_text = _hypothesis_reasoning_text(result)
    required_terms = expected.get("required_terms", [])
    missing = [term for term in required_terms if _norm(term) not in reasoning_text]
    add(
        "required_reasoning_concepts",
        not missing,
        10,
        "missing concepts: " + ", ".join(missing) if missing else "required concepts appear in hypothesis reasoning",
    )

    present = _forbidden_present(result, expected.get("forbidden_terms", []))
    add(
        "avoids_forbidden_conclusion",
        not present,
        10,
        "unsupported conclusion asserted: " + ", ".join(present) if present else "no unsupported conclusion asserted",
    )

    leading_class = result.get("leading_explanation", {}).get("evidence_class")
    allowed_classes = expected.get("allowed_evidence_classes", ["conclusion", "inference", "unknown"])
    add("evidence_class", leading_class in allowed_classes, 5, f"allowed {allowed_classes}, got {leading_class!r}")

    confidence = result.get("confidence", {}).get("level")
    allowed_confidence = expected.get("allowed_confidence", ["low", "medium", "high"])
    add("confidence_calibration", confidence in allowed_confidence, 5, f"allowed {allowed_confidence}, got {confidence!r}")

    validation = result.get("validation_plan", {})
    has_plan = all(bool(validation.get(field)) for field in ("target_metric", "review_timing", "comparison_method", "success_criteria"))
    add("intervention_validation", has_plan, 5, "validation plan complete" if has_plan else "validation plan incomplete")

    earned = sum(item.points for item in criteria if item.passed)
    possible = sum(item.points for item in criteria)
    pct = round(100 * earned / possible, 1) if possible else 0.0

    passed = (
        binding_ok
        and actual_status == expected_status
        and structure_ok
        and not present
        and pct >= expected.get("pass_score", 85)
    )

    return {
        "case_id": case.get("id"),
        "score": pct,
        "earned_points": earned,
        "possible_points": possible,
        "passed": passed,
        "criteria": [asdict(item) for item in criteria],
    }
