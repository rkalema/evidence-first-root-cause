from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class ActionRisk(str,Enum):
    READ_ONLY='read_only'
    REVERSIBLE_WRITE='reversible_write'
    EXTERNAL_WRITE='external_write'
    HIGH_IMPACT='high_impact'

@dataclass(frozen=True)
class ActionRequest:
    action:str
    risk:ActionRisk
    rationale:str

def requires_human_approval(request:ActionRequest)->bool:
    return request.risk in {ActionRisk.EXTERNAL_WRITE,ActionRisk.HIGH_IMPACT}
