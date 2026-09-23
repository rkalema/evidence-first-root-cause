from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import json
from .engine import InvestigationRun

def save_run(run:InvestigationRun,path:str|Path)->None:
    payload={'question':run.question,'stage':run.stage.value,'blocked_by':run.blocked_by,'context':run.context,'results':[{'role':r.role.value,'decision':r.decision.value,'summary':r.summary,'artifacts':r.artifacts,'evidence_ids':r.evidence_ids,'unknowns':r.unknowns,'next_requests':r.next_requests} for r in run.results],'events':[asdict(e) for e in run.events]}
    Path(path).write_text(json.dumps(payload,indent=2,default=str),encoding='utf-8')
