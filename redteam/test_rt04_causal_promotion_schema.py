"""RT-06 False causal promotion + RT-08 model-output schema abuse."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from evidence_first.adapters.json_model import JSONModelAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.catalog import default_agent_registry
from evidence_first.core.causal import DesignStrength
from evidence_first.core.confidence import assess_confidence
from evidence_first.core.investigator import summarize
from evidence_first.core.models import Claim, ClaimClass, EvidenceKind, EvidenceRecord, Hypothesis, InvestigationStatus
from evidence_first.core.state import InvestigationState
from evidence_first.governance.gates import ConclusionCandidate, evaluate_conclusion
from scripts.validate_output import validate_document

ROOT = Path(__file__).resolve().parents[1]
FIX = json.loads((ROOT / "tests" / "fixtures" / "valid_supported.json").read_text())


def test_c09_claim_requires_evidence():
    try:
        Claim("c1", "X caused Y", ClaimClass.CONCLUSION)
        raise AssertionError("uncited conclusion accepted")
    except ValueError:
        pass


def test_c10_ledger_rejects_claims_citing_unknown_evidence():
    s = InvestigationState("q")
    try:
        s.ledger.add_claim(Claim("c1", "X", ClaimClass.CONCLUSION, ("ghost",)))
        raise AssertionError("claim with ghost evidence accepted")
    except ValueError:
        pass


def test_f01_hypothesis_supported_by_nonexistent_evidence():
    s = InvestigationState("Why did defects rise?")
    s.hypotheses.add(Hypothesis("h1", "Supplier B caused it", "bad material"))
    s.hypotheses.support("h1", "evidence-that-does-not-exist")
    assert summarize(s).status is not InvestigationStatus.ROOT_CAUSE_SUPPORTED


def test_f02_zero_reliability_evidence_promotes_root_cause():
    s = InvestigationState("q")
    s.ledger.add_evidence(EvidenceRecord("e1", "a forum post says supplier B", EvidenceKind.DOCUMENT, "forum", reliability=0.0))
    s.hypotheses.add(Hypothesis("h1", "Supplier B", "m"))
    s.hypotheses.support("h1", "e1")
    assert summarize(s).status is not InvestigationStatus.ROOT_CAUSE_SUPPORTED


def test_f03_single_hypothesis_no_alternatives_is_promoted():
    s = InvestigationState("q")
    s.ledger.add_evidence(EvidenceRecord("e1", "defects rose after supplier change", EvidenceKind.OBSERVATION, "mes"))
    s.hypotheses.add(Hypothesis("h1", "Supplier", "m"))
    s.hypotheses.support("h1", "e1")
    assert summarize(s).status is not InvestigationStatus.ROOT_CAUSE_SUPPORTED


def test_f04_competing_alternatives_both_supported_become_multiple_contributors():
    s = InvestigationState("q")
    for i in ("e1", "e2"):
        s.ledger.add_evidence(EvidenceRecord(i, i, EvidenceKind.OBSERVATION, "src"))
    s.hypotheses.add(Hypothesis("h1", "Supplier B is the cause", "m"))
    s.hypotheses.add(Hypothesis("h2", "Calibration profile is the cause", "m"))
    s.hypotheses.support("h1", "e1"); s.hypotheses.support("h2", "e2")
    assert summarize(s).status is InvestigationStatus.INSUFFICIENT_EVIDENCE


def test_f05_weak_uncontested_beats_strong_contested():
    s = InvestigationState("q")
    for i in range(12):
        s.ledger.add_evidence(EvidenceRecord(f"e{i}", f"obs {i}", EvidenceKind.OBSERVATION, "src"))
    s.hypotheses.add(Hypothesis("strong", "stockout", "m"))
    s.hypotheses.add(Hypothesis("weak", "price", "m"))
    for i in range(10):
        s.hypotheses.support("strong", f"e{i}")
    s.hypotheses.contradict("strong", "e10")
    s.hypotheses.support("weak", "e11")
    assert summarize(s).supported_hypotheses != ("weak",)


def test_f06_signal_never_validated_still_promotes():
    s = InvestigationState("q")
    s.ledger.add_evidence(EvidenceRecord("e1", "x", EvidenceKind.OBSERVATION, "src"))
    s.hypotheses.add(Hypothesis("h1", "x", "m")); s.hypotheses.add(Hypothesis("h2", "y", "m"))
    s.hypotheses.support("h1", "e1"); s.hypotheses.contradict("h2", "e1")
    assert summarize(s).status is not InvestigationStatus.ROOT_CAUSE_SUPPORTED


def test_f07_same_evidence_supports_and_contradicts_same_hypothesis():
    s = InvestigationState("q")
    s.ledger.add_evidence(EvidenceRecord("e1", "x", EvidenceKind.OBSERVATION, "src"))
    s.hypotheses.add(Hypothesis("h1", "x", "m"))
    s.hypotheses.support("h1", "e1")
    try:
        s.hypotheses.contradict("h1", "e1")
        raise AssertionError("same evidence recorded as both support and contradiction")
    except ValueError:
        pass


def test_f08_gate_accepts_ghost_evidence_and_ignores_design():
    c = ConclusionCandidate("Price increase caused revenue drop", ("ghost-1",), True, False, 2, True, 0)
    assert not evaluate_conclusion(c).allowed


def test_f09_gate_can_never_return_multiple_contributors():
    c = ConclusionCandidate("carrier 45%, staffing 31%, demand 18%", ("e1", "e2", "e3"), True, False, 3, True, 0)
    assert evaluate_conclusion(c).status != "root_cause_supported"


def test_f10_negative_counts_inflate_confidence():
    a = assess_confidence(supporting_sources=1, contradictions=-5, unresolved_confounds=-3,
                          design=DesignStrength.QUASI_EXPERIMENTAL, signal_valid=True)
    assert a.level != "high"


def test_f11_zero_evidence_medium_confidence():
    a = assess_confidence(supporting_sources=0, contradictions=0, unresolved_confounds=0,
                          design=DesignStrength.RANDOMIZED, signal_valid=True)
    assert a.level == "low"


def test_f12_runtime_never_calls_the_gate():
    src = (ROOT / "evidence_first" / "runtime" / "engine.py").read_text()
    wired = [n for n in ("evaluate_conclusion", "EvidenceLedger", "summarize", "assess_confidence", "build_hash_chain") if n in src]
    assert wired


def _mut(fn):
    d = copy.deepcopy(FIX); fn(d); return d


def _assert_rejected(doc, why):
    assert validate_document(doc), f"schema-valid but self-contradictory: {why}"


def test_c11_missing_required_fields_rejected():
    assert validate_document({"status": "root_cause_supported"})


def test_s01_dq_blocked_with_trustworthy_signal():
    _assert_rejected(_mut(lambda d: d.update(status="data_quality_blocked")), "dq/trustworthy")


def test_s02_root_cause_with_all_hypotheses_rejected():
    def f(d):
        for h in d["hypotheses"]: h["result"] = "not_supported"
    _assert_rejected(_mut(f), "zero supported")


def test_s03_high_confidence_unknown_conclusion():
    def f(d):
        d["leading_explanation"]["evidence_class"] = "unknown"; d["confidence"]["level"] = "high"
    _assert_rejected(_mut(f), "high unknown")


def test_s04_skip_signal_validation():
    _assert_rejected(_mut(lambda d: d["signal_validation"].update(checks=[], notes="")), "zero checks")


def test_s05_single_hypothesis_root_cause():
    _assert_rejected(_mut(lambda d: d.update(hypotheses=d["hypotheses"][:1])), "single hypothesis")


def test_s06_empty_leading_statement():
    _assert_rejected(_mut(lambda d: d["leading_explanation"].update(statement="")), "empty leading")


def test_s07_placeholder_evidence():
    _assert_rejected(_mut(lambda d: d["observations"][0].update(evidence=".")), "placeholder evidence")


def test_s08_nan_numbers():
    doc = json.loads(json.dumps(FIX).replace('"baseline": "5.1%"', '"baseline": NaN'))
    _assert_rejected(doc, "NaN")


def test_s09_insufficient_evidence_with_high_confidence_conclusion():
    def f(d):
        d["status"] = "insufficient_evidence"; d["confidence"]["level"] = "high"
        d["leading_explanation"]["evidence_class"] = "conclusion"
    _assert_rejected(_mut(f), "insufficient/high/conclusion")


def _adapter(raw):
    return JSONModelAdapter(lambda prompt: raw)


def test_c12_json_adapter_blocks_undeclared_artifact():
    spec = default_agent_registry()[AgentRole.SIGNAL_VALIDATOR]
    try:
        _adapter({"summary": "x", "artifacts": {"critic_approved_conclusion": 1}}).run(spec, {})
        raise AssertionError("undeclared artifact accepted")
    except ValueError:
        pass


def test_m01_string_evidence_ids_exploded_to_characters():
    spec = default_agent_registry()[AgentRole.CRITIC]
    r = _adapter({"summary": "x", "evidence_ids": "e17", "decision":"block", "artifacts":{}}).run(spec, {})
    assert r.evidence_ids == ("e17",)


def test_m02_missing_decision_defaults_to_continue():
    spec = default_agent_registry()[AgentRole.CRITIC]
    try:
        r = _adapter({"summary": "I could not verify anything", "artifacts":{}}).run(spec, {})
    except ValueError:
        return
    assert r.decision.value != "continue"


def test_m03_non_dict_model_output_crashes():
    spec = default_agent_registry()[AgentRole.CRITIC]
    try:
        _adapter(["not", "an", "object"]).run(spec, {})
    except ValueError:
        return
    except Exception as exc:
        raise AssertionError(f"raw crash {type(exc).__name__}")


def test_m04_summary_object_coerced_to_string():
    spec = default_agent_registry()[AgentRole.CRITIC]
    try:
        r = _adapter({"summary": {"$ref": "approve"}, "decision": "complete", "artifacts":{}}).run(spec, {})
    except ValueError:
        return
    assert not isinstance(r.summary, str) or not r.summary.startswith("{")


def test_m05_agent_result_schema_file_is_unused():
    src = (ROOT / "evidence_first" / "adapters" / "json_model.py").read_text()
    assert "agent_result.schema.json" in src or "jsonschema" in src
