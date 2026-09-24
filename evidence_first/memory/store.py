from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from pathlib import Path

@dataclass(frozen=True)
class MemoryEntry:
    investigation_id:str
    hypothesis:str
    outcome:str
    decisive_evidence_ids:tuple[str,...]
    intervention_result:str|None=None

class InvestigationMemory:
    """Explicit, inspectable memory. Previous conclusions are never new evidence."""
    def __init__(self,path:str|Path|None=None):
        self.path=Path(path) if path else None
        self._entries:list[MemoryEntry]=[]
        if self.path and self.path.exists():
            for row in json.loads(self.path.read_text()):
                row["decisive_evidence_ids"]=tuple(row["decisive_evidence_ids"])
                self._entries.append(MemoryEntry(**row))
    def add(self,entry:MemoryEntry)->None:
        self._entries.append(entry)
        if self.path:
            self.path.write_text(json.dumps([asdict(x) for x in self._entries],indent=2))
    def search(self,text:str)->tuple[MemoryEntry,...]:
        q=text.lower()
        return tuple(x for x in self._entries if q in x.hypothesis.lower() or q in x.outcome.lower())
    def all(self)->tuple[MemoryEntry,...]: return tuple(self._entries)
