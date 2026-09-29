from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from .base import AgentRole

class AgentDecision(str, Enum):
    CONTINUE="continue"
    BLOCK="block"
    REVISE="revise"
    COMPLETE="complete"

@dataclass(frozen=True)
class AgentResult:
    role: AgentRole
    decision: AgentDecision
    summary: str
    artifacts: dict[str, Any]=field(default_factory=dict)
    evidence_ids: tuple[str,...]=()
    unknowns: tuple[str,...]=()
    next_requests: tuple[str,...]=()
