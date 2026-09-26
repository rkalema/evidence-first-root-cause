from __future__ import annotations

from dataclasses import dataclass

from evidence_first.core.causal import DesignStrength


@dataclass(frozen=True)
class ConclusionCandidate:
    statement: str
    evidence_ids: tuple[str, ...]
    signal_trustworthy: bool
    data_quality_blocked: bool
    competing_hypotheses_tested: int
    contradiction_review_complete: bool
    unresolved_material_confounds: int
    known_evidence_ids: tuple[str, ...] = ()
    design_strength: DesignStrength = DesignStrength.OBSERVATIONAL
    contributor_count: int = 1
    supporting_sources: int | None = None


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    status: str
    reasons: tuple[str, ...]


def evaluate_conclusion(candidate: ConclusionCandidate) -> GateResult:
    reasons: list[str] = []

    if candidate.data_quality_blocked:
        return GateResult(
            False,
            "data_quality_blocked",
            ("material data-quality issue blocks causal analysis",),
        )

    if not candidate.signal_trustworthy:
        reasons.append("signal not trustworthy")

    known = set(candidate.known_evidence_ids)
    if not candidate.evidence_ids:
        reasons.append("conclusion has no evidence citations")
    elif not known:
        reasons.append("conclusion evidence has not been resolved through the ledger")
    else:
        ghost = [eid for eid in candidate.evidence_ids if eid not in known]
        if ghost:
            reasons.append("conclusion cites unknown evidence: " + ", ".join(ghost))

    if candidate.competing_hypotheses_tested < 2:
        reasons.append("fewer than two competing hypotheses tested")
    if not candidate.contradiction_review_complete:
        reasons.append("contradiction review incomplete")
    if candidate.unresolved_material_confounds < 0:
        reasons.append("invalid negative confound count")
    elif candidate.unresolved_material_confounds > 0:
        reasons.append("material confounds remain unresolved")
    if candidate.contributor_count < 1:
        reasons.append("invalid contributor count")
    if candidate.design_strength < DesignStrength.OBSERVATIONAL:
        reasons.append("design strength is descriptive only")
    if candidate.supporting_sources is not None and candidate.supporting_sources <= 0:
        reasons.append("no supporting sources")

    if reasons:
        return GateResult(False, "insufficient_evidence", tuple(reasons))

    if candidate.contributor_count > 1:
        return GateResult(True, "multiple_contributors_supported", ())
    return GateResult(True, "root_cause_supported", ())
