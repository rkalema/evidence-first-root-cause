from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum

class DesignStrength(IntEnum):
    DESCRIPTIVE=1
    OBSERVATIONAL=2
    QUASI_EXPERIMENTAL=3
    RANDOMIZED=4

@dataclass(frozen=True)
class CausalDesignAssessment:
    strength:DesignStrength
    rationale:str
    limitations:tuple[str,...]=()
