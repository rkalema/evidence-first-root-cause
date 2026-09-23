from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

class SourceConnector(Protocol):
    def list_sources(self)->tuple[str,...]: ...
    def read_bytes(self,source_id:str)->bytes: ...

@dataclass
class InMemorySource:
    sources:dict[str,bytes]
    def list_sources(self)->tuple[str,...]: return tuple(sorted(self.sources))
    def read_bytes(self,source_id:str)->bytes: return self.sources[source_id]
