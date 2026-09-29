from __future__ import annotations

from dataclasses import dataclass

from .models import Hypothesis


@dataclass(frozen=True)
class ContradictionFinding:
    hypothesis_id: str
    survived: bool
    support_count: int
    contradiction_count: int
    reason: str


def review_hypothesis(hypothesis: Hypothesis) -> ContradictionFinding:
    support = len(hypothesis.supporting_evidence_ids)
    contradiction = len(hypothesis.contradicting_evidence_ids)

    survived = support > 0 and contradiction == 0
    if contradiction and support:
        reason = "Hypothesis has both supporting and contradicting evidence; preserve uncertainty."
    elif contradiction:
        reason = "Hypothesis is contradicted and has no supporting evidence."
    elif support:
        reason = "Hypothesis currently survives the recorded contradiction checks."
    else:
        reason = "Hypothesis remains untested."

    return ContradictionFinding(
        hypothesis_id=hypothesis.hypothesis_id,
        survived=survived,
        support_count=support,
        contradiction_count=contradiction,
        reason=reason,
    )
