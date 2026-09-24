from evidence_first.core.contradiction import review_hypothesis
from evidence_first.core.investigator import summarize
from evidence_first.core.ledger import EvidenceLedger
from evidence_first.core.models import Claim, ClaimClass, EvidenceKind, EvidenceRecord, Hypothesis, HypothesisStatus, InvestigationStatus
from evidence_first.core.state import InvestigationState


def record(eid: str, statement: str = "evidence") -> EvidenceRecord:
    return EvidenceRecord(eid, statement, EvidenceKind.OBSERVATION, "test")


def test_ledger_rejects_duplicate_evidence() -> None:
    ledger = EvidenceLedger()
    ledger.add_evidence(record("e1"))
    try:
        ledger.add_evidence(record("e1"))
        assert False
    except ValueError:
        pass


def test_claim_must_reference_known_evidence() -> None:
    ledger = EvidenceLedger()
    ledger.add_evidence(record("e1"))
    claim = Claim("c1", "supported claim", ClaimClass.INFERENCE, ("e1",))
    ledger.add_claim(claim)
    assert ledger.claim("c1") == claim


def test_non_unknown_claim_requires_evidence() -> None:
    try:
        Claim("c1", "unsupported", ClaimClass.CONCLUSION)
        assert False
    except ValueError:
        pass


def test_hypothesis_with_only_contradiction_is_rejected() -> None:
    h = Hypothesis("h1", "plugin caused failure", "broken routing")
    h.contradicting_evidence_ids.append("e1")
    assert h.evaluate() is HypothesisStatus.NOT_SUPPORTED
    assert review_hypothesis(h).survived is False


def test_hypothesis_with_support_and_contradiction_preserves_uncertainty() -> None:
    h = Hypothesis("h1", "mixed explanation", "mechanism")
    h.supporting_evidence_ids.append("e1")
    h.contradicting_evidence_ids.append("e2")
    assert h.evaluate() is HypothesisStatus.PARTIALLY_SUPPORTED


def test_summary_returns_root_cause_when_one_hypothesis_survives() -> None:
    state = InvestigationState("What caused the incident?")
    state.ledger.add_evidence(record("e1"))
    state.ledger.add_evidence(record("e2"))
    state.hypotheses.add(Hypothesis("h1", "cause A", "mechanism A"))
    state.hypotheses.add(Hypothesis("h2", "cause B", "mechanism B"))
    state.hypotheses.support("h1", "e1")
    state.hypotheses.contradict("h2", "e2")
    result = summarize(state)
    assert result.status is InvestigationStatus.ROOT_CAUSE_SUPPORTED
    assert result.supported_hypotheses == ("h1",)
    assert result.rejected_hypotheses == ("h2",)


def test_summary_returns_multiple_contributors_when_multiple_survive() -> None:
    state = InvestigationState("Why did SLA fall?")
    state.ledger.add_evidence(record("e1"))
    state.ledger.add_evidence(record("e2"))
    state.hypotheses.add(Hypothesis("h1", "volume", "capacity load"))
    state.hypotheses.add(Hypothesis("h2", "labor", "capacity loss"))
    state.hypotheses.support("h1", "e1")
    state.hypotheses.support("h2", "e2")
    result = summarize(state)
    assert result.status is InvestigationStatus.MULTIPLE_CONTRIBUTORS_SUPPORTED


def test_explicit_data_quality_block_overrides_inference() -> None:
    state = InvestigationState("Why did mortality double?")
    state.mark_data_quality_blocked("denominator feed incomplete")
    result = summarize(state)
    assert result.status is InvestigationStatus.DATA_QUALITY_BLOCKED
