from __future__ import annotations
from typing import Protocol
from evidence_first.agents.base import AgentSpec
from evidence_first.agents.result import AgentResult

class AgentAdapter(Protocol):
    def run(self, spec: AgentSpec, context: dict[str, object]) -> AgentResult:
        ...
