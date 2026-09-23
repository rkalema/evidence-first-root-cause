from __future__ import annotations
from collections.abc import Callable
from typing import Any
from evidence_first.agents.base import AgentSpec
from evidence_first.agents.result import AgentDecision,AgentResult
from evidence_first.security import UNTRUSTED_SOURCE_POLICY
from .prompt import render_agent_prompt

ModelCall=Callable[[str],dict[str,Any]]

class CallableJSONAdapter:
    def __init__(self,call:ModelCall): self.call=call
    def run(self,spec:AgentSpec,context:dict[str,object])->AgentResult:
        raw=self.call(UNTRUSTED_SOURCE_POLICY+'\n\n'+render_agent_prompt(spec,context))
        decision=AgentDecision(raw.get('decision','continue'))
        return AgentResult(spec.role,decision,str(raw.get('summary','')),dict(raw.get('artifacts',{})),tuple(raw.get('evidence_ids',())),tuple(raw.get('unknowns',())),tuple(raw.get('next_requests',())))
