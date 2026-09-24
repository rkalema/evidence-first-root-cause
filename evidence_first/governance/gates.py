from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ConclusionCandidate:
    statement:str
    evidence_ids:tuple[str,...]
    signal_trustworthy:bool
    data_quality_blocked:bool
    competing_hypotheses_tested:int
    contradiction_review_complete:bool
    unresolved_material_confounds:int

@dataclass(frozen=True)
class GateResult:
    allowed:bool
    status:str
    reasons:tuple[str,...]

def evaluate_conclusion(candidate:ConclusionCandidate)->GateResult:
    reasons=[]
    if candidate.data_quality_blocked:
        return GateResult(False,'data_quality_blocked',('material data-quality issue blocks causal analysis',))
    if not candidate.signal_trustworthy: reasons.append('signal not trustworthy')
    if not candidate.evidence_ids: reasons.append('conclusion has no evidence citations')
    if candidate.competing_hypotheses_tested<2: reasons.append('fewer than two competing hypotheses tested')
    if not candidate.contradiction_review_complete: reasons.append('contradiction review incomplete')
    if candidate.unresolved_material_confounds>0: reasons.append('material confounds remain unresolved')
    if reasons: return GateResult(False,'insufficient_evidence',tuple(reasons))
    return GateResult(True,'root_cause_supported',())
