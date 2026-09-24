import json
from pathlib import Path

CASES=Path(__file__).resolve().parents[1]/'benchmarks'/'cases'

def test_benchmark_corpus_has_at_least_twenty_cases():
    assert len(list(CASES.glob('*.json')))>=20

def test_every_case_has_hidden_expectations_and_required_fields():
    allowed={'root_cause_supported','multiple_contributors_supported','insufficient_evidence','data_quality_blocked'}
    for p in CASES.glob('*.json'):
        c=json.loads(p.read_text())
        expected=c['expected']
        assert {'id','title','prompt','facts','expected'}<=set(c)
        assert expected['status'] in allowed
        assert c['facts']
        minimum=1 if expected['status']=='data_quality_blocked' else 2
        assert expected['min_hypotheses']>=minimum
