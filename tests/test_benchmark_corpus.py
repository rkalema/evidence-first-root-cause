import json
from pathlib import Path

CASES=Path(__file__).resolve().parents[1]/'benchmarks'/'cases'

def test_benchmark_corpus_has_at_least_twenty_cases():
    assert len(list(CASES.glob('*.json')))>=20

def test_every_case_has_hidden_expectations_and_required_fields():
    allowed={'root_cause_supported','multiple_contributors_supported','insufficient_evidence','data_quality_blocked'}
    for p in CASES.glob('*.json'):
        c=json.loads(p.read_text())
        assert {'id','title','prompt','facts','expected'}<=set(c)
        assert c['expected']['status'] in allowed
        assert c['facts']
        assert c['expected']['min_hypotheses']>=2
