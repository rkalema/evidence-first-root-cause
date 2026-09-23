from __future__ import annotations
from collections.abc import Callable
from evidence_first.agents.base import AgentSpec
from evidence_first.agents.result import AgentResult

class CallableAdapter:
    """Provider-neutral adapter for Claude, Codex, APIs, or local test doubles."""
    def __init__(self, fn: Callable[[AgentSpec, dict[str, object]], AgentResult]):
        self.fn=fn

    def run(self, spec: AgentSpec, context: dict[str, object]) -> AgentResult:
        result=self.fn(spec, context)
        if result.role is not spec.role:
            raise ValueError(f"adapter returned {result.role} for {spec.role}")
        return result
