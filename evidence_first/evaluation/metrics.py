from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationAggregate:
    n: int
    mean_score: float
    pass_rate: float
    false_causal_rate: float
    insufficient_evidence_accuracy: float
    data_quality_stop_accuracy: float


def aggregate_scores(rows: list[dict]) -> EvaluationAggregate:
    if not rows:
        return EvaluationAggregate(0, 0, 0, 0, 0, 0)

    n = len(rows)
    mean = sum(float(r.get("score", 0)) for r in rows) / n
    pass_rate = sum(bool(r.get("passed")) for r in rows) / n

    noncausal_expected = {"insufficient_evidence", "data_quality_blocked"}
    causal_actual = {"root_cause_supported", "multiple_contributors_supported"}
    false_causal = sum(
        (
            r.get("expected_status") in noncausal_expected
            and r.get("actual_status") in causal_actual
        )
        or bool(r.get("false_causal_conclusion"))
        for r in rows
    ) / n

    insufficient = [r for r in rows if r.get("expected_status") == "insufficient_evidence"]
    dq = [r for r in rows if r.get("expected_status") == "data_quality_blocked"]

    ie_acc = (
        sum(r.get("actual_status") == "insufficient_evidence" for r in insufficient)
        / len(insufficient)
        if insufficient
        else 0
    )
    dq_acc = (
        sum(r.get("actual_status") == "data_quality_blocked" for r in dq)
        / len(dq)
        if dq
        else 0
    )
    return EvaluationAggregate(
        n,
        round(mean, 2),
        round(pass_rate, 4),
        round(false_causal, 4),
        round(ie_acc, 4),
        round(dq_acc, 4),
    )
