from __future__ import annotations

from dataclasses import dataclass

from .causal import DesignStrength


@dataclass(frozen=True)
class ConfidenceAssessment:
    level: str
    score: int
    reasons: tuple[str, ...]


def assess_confidence(
    *,
    supporting_sources: int,
    contradictions: int,
    unresolved_confounds: int,
    design: DesignStrength,
    signal_valid: bool,
) -> ConfidenceAssessment:
    counts = {
        "supporting_sources": supporting_sources,
        "contradictions": contradictions,
        "unresolved_confounds": unresolved_confounds,
    }
    if any(not isinstance(v, int) or v < 0 for v in counts.values()):
        return ConfidenceAssessment(
            "low",
            0,
            ("invalid negative/non-integer evidence counts",),
        )
    if not signal_valid:
        return ConfidenceAssessment("low", 0, ("signal not validated",))
    if supporting_sources == 0:
        return ConfidenceAssessment("low", 0, ("no supporting sources",))

    score = (
        min(45, supporting_sources * 10)
        + int(design) * 10
        - contradictions * 15
        - unresolved_confounds * 10
    )
    score = max(0, min(100, score))

    if (
        score >= 70
        and design >= DesignStrength.QUASI_EXPERIMENTAL
        and contradictions == 0
        and unresolved_confounds == 0
    ):
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"

    reasons = (
        f"{supporting_sources} supporting source(s)",
        f"{contradictions} contradiction(s)",
        f"{unresolved_confounds} unresolved confound(s)",
        f"design={design.name.lower()}",
    )
    return ConfidenceAssessment(level, score, reasons)
