from evidence_first.evaluation.record import ExperimentLedger,RunRecord

def test_experiment_ledger_roundtrip(tmp_path):
    p=tmp_path/'runs.jsonl'; l=ExperimentLedger(p)
    r=RunRecord('c','baseline','m','sha','p','o',88.0,True,1.2,100,50,0)
    l.append(r)
    assert l.read()==(r,)
