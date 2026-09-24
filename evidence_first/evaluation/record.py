from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import json,time

@dataclass(frozen=True)
class RunRecord:
    case_id:str
    condition:str
    model:str
    repository_sha:str
    prompt_path:str
    output_path:str
    score:float
    passed:bool
    elapsed_seconds:float|None=None
    input_tokens:int|None=None
    output_tokens:int|None=None
    tool_calls:int|None=None

class ExperimentLedger:
    def __init__(self,path:str|Path): self.path=Path(path)
    def append(self,record:RunRecord)->None:
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('a',encoding='utf-8') as f:
            f.write(json.dumps(asdict(record),sort_keys=True)+'\n')
    def read(self)->tuple[RunRecord,...]:
        if not self.path.exists(): return ()
        return tuple(RunRecord(**json.loads(line)) for line in self.path.read_text().splitlines() if line.strip())
