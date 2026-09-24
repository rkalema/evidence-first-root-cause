from __future__ import annotations

from dataclasses import dataclass

from .contradiction import ContradictionFinding, review_hypothesis
from .models import HypothesisStatus, InvestigationStatus
from .state import InvestigationState


@dataclass(frozen=True)
class InvestigationSummary:
    status: InvestigationStatus
    supported_hypotheses: tuple[str, ...]
    partially_supported_hypotheses: tuple[str, ...]
    rejected_hypotheses: tuple[str, ...]
    untested_hypotheses: tuple[str, ...]
    contradiction_findings: tuple[ContradictionFinding, ...]
    unknowns: tuple[str, ...]


def summarize(state: InvestigationState) -> InvestigationSummary:
    groups = {
        HypothesisStatus.SUPPORTED: [],
        HypothesisStatus.PARTIALLY_SUPPORTED: [],
        HypothesisStatus.NOT_SUPPORTED: [],
        HypothesisStatus.UNTESTED: [],
    }
    findings: list[ContradictionFinding] = []

    for hypothesis in state.hypotheses.all:
        status = state.hypotheses.evaluate(hypothesis.hypothesis_id)
        groups[status].append(hypothesis.hypothesis_id)
        findings.append(review_hypothesis(hypothesis))

    status = state.status
    if status is InvestigationStatus.OPEN:
        if not state.signal_validated:
            status = InvestigationStatus.INSUFFICIENT_EVIDENCE
        elif state.hypotheses.invalid_evidence_refs:
            status = InvestigationStatus.INSUFFICIENT_EVIDENCE
        elif len(state.hypotheses.all) < state.minimum_competing_hypotheses:
            status = InvestigationStatus.INSUFFICIENT_EVIDENCE
        else:
            supported = [
                state.hypotheses.get(hid)
                for hid in groups[HypothesisStatus.SUPPORTED]
            ]
            if len(supported) == 1:
                status = InvestigationStatus.ROOT_CAUSE_SUPPORTED
            elif len(supported) > 1:
                if all(h.relationship == "additive" for h in supported):
                    status = InvestigationStatus.MULTIPLE_CONTRIBUTORS_SUPPORTED
                else:
                    status = InvestigationStatus.INSUFFICIENT_EVIDENCE
            else:
                status = InvestigationStatus.INSUFFICIENT_EVIDENCE

    return InvestigationSummary(
        status=status,
        supported_hypotheses=tuple(groups[HypothesisStatus.SUPPORTED]),
        partially_supported_hypotheses=tuple(groups[HypothesisStatus.PARTIALLY_SUPPORTED]),
        rejected_hypotheses=tuple(groups[HypothesisStatus.NOT_SUPPORTED]),
        untested_hypotheses=tuple(groups[HypothesisStatus.UNTESTED]),
        contradiction_findings=tuple(findings),
        unknowns=tuple(state.unknowns),
    )
