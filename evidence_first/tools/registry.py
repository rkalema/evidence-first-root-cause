from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class ToolSpec:
    name:str
    description:str
    read_only:bool
    handler:Callable[...,Any]

class ToolRegistry:
    def __init__(self)->None:
        self._tools:dict[str,ToolSpec]={}
    def register(self,spec:ToolSpec)->None:
        if spec.name in self._tools: raise ValueError(f"duplicate tool: {spec.name}")
        self._tools[spec.name]=spec
    def get(self,name:str)->ToolSpec: return self._tools[name]
    def names(self)->tuple[str,...]: return tuple(sorted(self._tools))
