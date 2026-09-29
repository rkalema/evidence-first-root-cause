"""RT-12 Benchmark leakage + scorer gaming across the full 20-case corpus."""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.evaluate_case import score
from scripts.evaluate_runner import prompt_packet, compare
from scripts.validate_output import validate_document

ROOT = Path(__file__).resolve().parents[1]
CASES = {json.loads(p.read_text())["id"]: json.loads(p.read_text()) for p in sorted((ROOT / "benchmarks" / "cases").glob("*.json"))}
IDS = sorted(CASES)
TEMPLATE = json.loads((ROOT / "tests" / "fixtures" / "valid_supported.json").read_text())


def _packet_text(cid):
    return json.dumps([prompt_packet(cid, "baseline"), prompt_packet(cid, "evidence-first")]).lower()


# ------------------------------------------------------------------ corpus integrity (controls)
def test_c18_corpus_has_20_unique_cases_matching_filenames():
    files = sorted((ROOT / "benchmarks" / "cases").glob("*.json"))
    assert len(files) == 20 and len(CASES) == 20
    assert all(json.loads(p.read_text())["id"] == p.stem for p in files)


@pytest.mark.parametrize("cid", IDS)
def test_c19_prompt_packet_excludes_expected_block(cid):
    t = _packet_text(cid)
    assert '"expected"' not in t and "pass_score" not in t and "forbidden_terms" not in t


@pytest.mark.parametrize("cid", IDS)
def test_c20_forbidden_conclusions_not_in_packet(cid):
    t = _packet_text(cid)
    leaked = [f for f in CASES[cid]["expected"]["forbidden_terms"] if f.lower() in t]
    assert not leaked, f"forbidden phrase appears in the model's own prompt: {leaked}"


# ------------------------------------------------------------------ leakage channels
def test_l01_install_skill_ships_gold_answers_to_the_agent(tmp_path):
    """README: install the whole repo as the agent's skill folder. install_skill.py copies benchmarks/cases
    (with 'expected') into the directory the agent under test can read."""
    dest = tmp_path / "skills" / "evidence-first-root-cause"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "install_skill.py"), str(dest)], check=True, capture_output=True)
    leaked = [p.name for p in (dest / "benchmarks" / "cases").glob("*.json") if "expected" in json.loads(p.read_text())]
    assert not leaked, f"{len(leaked)}/20 gold keys installed inside the agent's skill directory"


def test_l02_skill_install_also_ships_scorer_and_tests(tmp_path):
    dest = tmp_path / "s"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "install_skill.py"), str(dest)], check=True, capture_output=True)
    present = [p for p in ("scripts/evaluate_case.py", "tests/test_evaluator.py", "benchmarks/CATALOG.md") if (dest / p).exists()]
    assert not present, f"agent can read scorer logic / trap catalog: {present}"


def test_l03_catalog_names_every_trap():
    """CATALOG.md maps each case id to its trap ('broken denominator', 'selection bias ...') — an answer key in prose."""
    text = (ROOT / "benchmarks" / "CATALOG.md").read_text()
    named = sum(1 for cid in IDS if cid in text)
    assert named == 0, f"CATALOG.md reveals the trap for {named}/20 cases"


@pytest.mark.parametrize("cid", IDS)
def test_l04_required_terms_are_free_by_echoing_facts(cid):
    """If every required term appears verbatim in the prompt/facts, the 15-point 'required evidence'
    criterion rewards copy-paste, not reasoning."""
    t = (CASES[cid]["prompt"] + " " + " ".join(CASES[cid]["facts"])).lower()
    req = CASES[cid]["expected"]["required_terms"]
    free = [r for r in req if r.lower() in t]
    assert len(free) < len(req), f"all required terms {req} are verbatim in the facts"


def test_l05_evidence_first_condition_never_receives_the_method():
    ef = prompt_packet("price-vs-stockout", "evidence-first")
    method_markers = ["validate the signal", "competing hypotheses", "data_quality_blocked"]
    got = [m for m in method_markers if m in (ef["system"] + ef["user"]).lower()]
    assert got, f"Pass-B system prompt is {len(ef['system'])} chars and contains none of SKILL.md's method: {ef['system']!r}"


def test_l06_no_integrity_manifest_for_gold_files():
    manifests = list(ROOT.glob("benchmarks/*.sha256")) + list(ROOT.glob("benchmarks/*manifest*"))
    assert manifests, "no hash manifest; editing a case's pass_score or expected status is undetectable"


# ------------------------------------------------------------------ scorer gaming
def _build(case, status, conf, cls, leading, extra_terms=()):
    d = copy.deepcopy(TEMPLATE)
    d["status"] = status
    d["signal_validation"]["trustworthy"] = status != "data_quality_blocked"
    d["hypotheses"] = [dict(TEMPLATE["hypotheses"][0], hypothesis=f"Generic hypothesis {i}") for i in range(4)]
    d["observations"] = [{"statement": f, "evidence": "supplied fact"} for f in case["facts"]]
    d["leading_explanation"] = {"statement": leading, "evidence_class": cls}
    d["confidence"]["level"] = conf
    d["unknowns"] = list(extra_terms)
    return d


STATUS_DEFAULTS = {
    "root_cause_supported": ("high", "conclusion"),
    "multiple_contributors_supported": ("medium", "conclusion"),
    "insufficient_evidence": ("low", "unknown"),
    "data_quality_blocked": ("low", "unknown"),
}


def keyword_status(case):
    """A 6-line heuristic with no causal reasoning."""
    t = (case["prompt"] + " " + " ".join(case["facts"])).lower()
    if re.search(r"denominator|feed|label|mature|consent|definition|interface|not flag|stale", t):
        return "data_quality_blocked"
    if re.search(r"unavailable|missing for|not randomi|no holdout|self-selected|not logged|audit", t):
        return "insufficient_evidence"
    if len(re.findall(r"\d+%", t)) >= 5 and re.search(r"explain|share|mix", t):
        return "multiple_contributors_supported"
    return "root_cause_supported"


def _run_policy(policy):
    passed = []
    for cid in IDS:
        case = CASES[cid]
        doc = policy(case)
        assert not validate_document(doc), validate_document(doc)
        if score(case, doc)["passed"]:
            passed.append(cid)
    return passed


def test_g01_constant_status_facts_echo_policy():
    pol = lambda c: _build(c, "root_cause_supported", "high", "conclusion", "The leading explanation is documented above.")
    p = _run_policy(pol)
    assert len(p) <= 2, f"zero-reasoning constant policy passes {len(p)}/20: {p}"


def test_g02_keyword_classifier_policy():
    def pol(c):
        st = keyword_status(c); conf, cls = STATUS_DEFAULTS[st]
        return _build(c, st, conf, cls, "See observations.")
    p = _run_policy(pol)
    assert len(p) <= 5, f"regex status classifier + fact echo passes {len(p)}/20 cases: {sorted(set(IDS)-set(p))} failed"


def test_g03_four_static_files_pass_the_whole_corpus():
    """One pre-written JSON per status (no case knowledge beyond the 4-way label) with every case's
    required terms stuffed into 'unknowns'. compare()/score() never bind a result to its case."""
    all_terms = sorted({t for c in CASES.values() for t in c["expected"]["required_terms"]})
    universal = {st: _build({"facts": ["n/a"]}, st, *STATUS_DEFAULTS[st], "Evidence reviewed.", all_terms) for st in STATUS_DEFAULTS}
    # multiple-contributor cases each allow only 'medium' confidence
    passes = [cid for cid in IDS if score(CASES[cid], universal[CASES[cid]["expected"]["status"]])["passed"]]
    assert len(passes) <= 2, f"4 static answer files pass {len(passes)}/20 cases"


@pytest.mark.parametrize("cid", IDS)
def test_g04_forbidden_claim_smuggled_outside_leading_explanation(cid):
    """Gold-correct answer, but the forbidden causal claim is asserted in impact.summary and in
    recommended actions. Secure: penalised. Actual: forbidden terms are only checked in leading_explanation."""
    case = CASES[cid]; e = case["expected"]
    doc = _build(case, e["status"], e["allowed_confidence"][0], e["allowed_evidence_classes"][0], "Evidence reviewed.", e["required_terms"])
    claim = e["forbidden_terms"][0]
    doc["impact"]["summary"] = f"Bottom line for leadership: {claim} the change."
    doc["recommended_actions"]["corrective"] = [f"Act on the finding that {claim} the change."]
    assert not score(case, doc)["passed"], f"'{claim}' asserted to leadership, still passes"


@pytest.mark.parametrize("cid", IDS)
def test_g05_paraphrased_forbidden_conclusion_evades(cid):
    case = CASES[cid]; e = case["expected"]
    forb = e["forbidden_terms"][0]
    para = re.sub(r"\bcaused\b", "was responsible for", forb, flags=re.I)
    if para == forb:
        para = forb.replace(" ", " ")  # non-breaking spaces
    doc = _build(case, e["status"], e["allowed_confidence"][0], e["allowed_evidence_classes"][0], para + " the change.", e["required_terms"])
    assert not score(case, doc)["passed"], f"leading explanation {para!r} evades forbidden {forb!r}"


def test_g06_answer_reuse_across_cases_accepted(tmp_path):
    """compare() scores any file against any case id — no case_id binding or content hash in the result."""
    case = CASES["price-vs-stockout"]; e = case["expected"]
    good = _build(case, e["status"], "high", "conclusion", "Stockout drove the decline", e["required_terms"])
    f = tmp_path / "a.json"; f.write_text(json.dumps(good))
    reuse = compare("supplier-delay-port", f, f)
    assert "error" in json.dumps(reuse).lower() or not reuse["evidence_first"]["valid_schema"], \
        f"a price-vs-stockout answer was scored for supplier-delay-port without complaint (score {reuse['evidence_first']['score']})"


def test_g07_false_causal_rate_metric_is_always_zero():
    from evidence_first.evaluation.metrics import aggregate_scores
    rows = [{"score": 90, "passed": True, "expected_status": "insufficient_evidence", "actual_status": "root_cause_supported"}]
    agg = aggregate_scores(rows)
    assert agg.false_causal_rate > 0, "a root-cause claim on an insufficient-evidence case counts as false_causal_rate=0.0 (field never populated)"


@pytest.mark.parametrize("cid", IDS)
def test_g08_correct_negation_is_penalised(cid):
    """A CORRECT answer that explicitly rejects the trap ('the evidence does not show that X caused ...')
    trips the substring filter. Secure: negated rejection is not penalised."""
    case = CASES[cid]; e = case["expected"]
    forb = e["forbidden_terms"][0]
    lead = f"The evidence does not support the claim that {forb} the change; the alternative explanation survives testing."
    doc = _build(case, e["status"], e["allowed_confidence"][0], e["allowed_evidence_classes"][0], lead, e["required_terms"])
    rep = score(case, doc)
    crit = next(c for c in rep["criteria"] if c["name"] == "avoids_forbidden_conclusion")
    assert crit["passed"], f"correct rejection of '{forb}' lost 10 points (score {rep['score']}, passed={rep['passed']})"