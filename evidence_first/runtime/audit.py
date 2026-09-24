from __future__ import annotations
from dataclasses import asdict
import hashlib,json
from .events import InvestigationEvent

def hash_event(event:InvestigationEvent,previous_hash:str='')->str:
    payload={'previous_hash':previous_hash,'event':asdict(event)}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()

def build_hash_chain(events:list[InvestigationEvent])->tuple[str,...]:
    chain=[]; prev=''
    for event in events:
        prev=hash_event(event,prev); chain.append(prev)
    return tuple(chain)

def verify_hash_chain(events:list[InvestigationEvent],chain:tuple[str,...])->bool:
    return build_hash_chain(events)==chain
