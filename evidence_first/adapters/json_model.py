from __future__ import annotations
import json
from collections.abc import Callable
from typing import Any
from evidence_first.agents.base import AgentSpec
from evidence_first.agents.result import AgentDecision,AgentResult
from evidence_first.agents.validation import validate_agent_result
from .prompt_builder import build_agent_prompt

JSONCall=Callable[[str],dict[str,Any]]

class JSONModelAdapter:
    """Provider-neutral structured adapter for model APIs or local harnesses."""
    def __init__(self,call:JSONCall): self.call=call
    def run(self,spec:AgentSpec,context:dict[str,object])->AgentResult:
        context_summary=json.dumps(context,sort_keys=True,default=str)
        raw=self.call(build_agent_prompt(spec,context_summary))
        result=AgentResult(
            role=spec.role,
            decision=AgentDecision(raw.get('decision','continue')),
            summary=str(raw.get('summary','')),
            artifacts=dict(raw.get('artifacts',{})),
            evidence_ids=tuple(raw.get('evidence_ids',())),
            unknowns=tuple(raw.get('unknowns',())),
            next_requests=tuple(raw.get('next_requests',())),
        )
        violations=validate_agent_result(spec,result)
        if violations:
            raise ValueError('; '.join(v.message for v in violations))
        return result
