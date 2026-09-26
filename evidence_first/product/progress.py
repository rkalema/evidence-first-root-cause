from __future__ import annotations

from collections import defaultdict
from typing import TextIO

from evidence_first.agents.base import AgentRole, AgentSpec
from evidence_first.agents.orchestrator import InvestigationOrchestrator
from evidence_first.agents.result import AgentResult


class ProgressAdapter:
    """User-facing progress wrapper around any governed agent adapter."""

    def __init__(self, inner, *, stream: TextIO):
        self.inner = inner
        self.stream = stream
        plan = InvestigationOrchestrator().build_plan()
        self.position = {task.role: index for index, task in enumerate(plan.tasks, start=1)}
        self.total = len(plan.tasks)
        self.calls = defaultdict(int)

    @staticmethod
    def _label(role: AgentRole) -> str:
        return role.value.replace("_", " ").title()

    def run(self, spec: AgentSpec, context: dict[str, object]) -> AgentResult:
        self.calls[spec.role] += 1
        position = self.position[spec.role]
        suffix = (
            ""
            if self.calls[spec.role] == 1
            else f" (analysis round {self.calls[spec.role]})"
        )
        print(
            f"[{position}/{self.total}] {self._label(spec.role)}{suffix} ...",
            file=self.stream,
            flush=True,
        )
        result = self.inner.run(spec, context)
        print(
            f"    -> {result.decision.value}: {result.summary[:160]}",
            file=self.stream,
            flush=True,
        )
        return result
