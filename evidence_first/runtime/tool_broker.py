from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from evidence_first.tools.registry import ToolRegistry

@dataclass(frozen=True)
class ToolRequest:
    name:str
    arguments:dict[str,Any]
    source_ids:tuple[str,...]=()

@dataclass(frozen=True)
class ToolOutcome:
    name:str
    ok:bool
    value:Any=None
    error:str|None=None
    source_ids:tuple[str,...]=()

class ToolExecutionBroker:
    def __init__(self,registry:ToolRegistry): self.registry=registry
    def execute(self,request:ToolRequest)->ToolOutcome:
        try: spec=self.registry.get(request.name)
        except KeyError: return ToolOutcome(request.name,False,error='tool not registered',source_ids=request.source_ids)
        if not spec.read_only:
            return ToolOutcome(request.name,False,error='automatic execution denied for non-read-only tool',source_ids=request.source_ids)
        try:
            value=spec.handler(**request.arguments)
            return ToolOutcome(request.name,True,value=value,source_ids=request.source_ids)
        except Exception as exc:
            return ToolOutcome(request.name,False,error=f'{type(exc).__name__}: {exc}',source_ids=request.source_ids)
    def execute_many(self,requests:list[ToolRequest])->tuple[ToolOutcome,...]:
        return tuple(self.execute(r) for r in requests)
