from evidence_first.core.causal import DesignStrength
from evidence_first.core.confidence import assess_confidence
from evidence_first.governance.gates import ConclusionCandidate,evaluate_conclusion
from evidence_first.runtime.audit import build_hash_chain,verify_hash_chain
from evidence_first.runtime.events import InvestigationEvent

def test_conclusion_gate_blocks_unresolved_confounds():
    c=ConclusionCandidate('x',('e1',),True,False,2,True,1)
    r=evaluate_conclusion(c)
    assert not r.allowed and r.status=='insufficient_evidence'

def test_data_quality_gate_wins():
    c=ConclusionCandidate('x',(),False,True,0,False,3)
    assert evaluate_conclusion(c).status=='data_quality_blocked'

def test_confidence_respects_design_strength():
    r=assess_confidence(supporting_sources=5,contradictions=0,unresolved_confounds=0,design=DesignStrength.OBSERVATIONAL,signal_valid=True)
    assert r.level!='high'

def test_audit_hash_chain_detects_change():
    events=[InvestigationEvent('x','s','m','a'),InvestigationEvent('y','s','n','b')]
    chain=build_hash_chain(events)
    assert verify_hash_chain(events,chain)
    changed=[events[0],InvestigationEvent('y','s','tampered','b')]
    assert not verify_hash_chain(changed,chain)
