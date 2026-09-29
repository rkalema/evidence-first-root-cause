from __future__ import annotations
from collections.abc import Callable
from evidence_first.agents.base import AgentRole, AgentSpec
from evidence_first.agents.result import AgentDecision, AgentResult

Handler=Callable[[AgentSpec,dict[str,object]],AgentResult]

class ScriptedAdapter:
    """Deterministic adapter for tests and reproducible benchmark runs."""
    def __init__(self, handlers: dict[AgentRole,Handler]):
        self.handlers=handlers
    def run(self,spec:AgentSpec,context:dict[str,object])->AgentResult:
        if spec.role not in self.handlers:
            return AgentResult(spec.role,AgentDecision.BLOCK,f"No handler for {spec.role.value}")
        return self.handlers[spec.role](spec,context)
