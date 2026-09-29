from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from .events import InvestigationEvent


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(k): _canonical(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, (set, frozenset)):
        values = [_canonical(v) for v in value]
        return sorted(values, key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(value, Decimal):
        return {"__type__": "Decimal", "value": str(value)}
    if isinstance(value, str):
        return {"__type__": "str", "value": value}
    if isinstance(value, bool):
        return {"__type__": "bool", "value": value}
    if isinstance(value, int):
        return {"__type__": "int", "value": value}
    if isinstance(value, float):
        return {"__type__": "float", "value": repr(value)}
    if value is None:
        return {"__type__": "None", "value": None}
    raise TypeError(f"unsupported audit value: {type(value).__name__}")


def hash_event(event: InvestigationEvent, previous_hash: str = "") -> str:
    payload = {
        "previous_hash": previous_hash,
        "event": {
            "event_type": event.event_type,
            "stage": event.stage,
            "message": event.message,
            "actor": event.actor,
            "metadata": _canonical(event.metadata),
            # Signature and timestamp are deliberately excluded from the public
            # deterministic chain. The event HMAC authenticates those fields.
        },
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_hash_chain(events: list[InvestigationEvent]) -> tuple[str, ...]:
    chain: list[str] = []
    previous = ""
    for event in events:
        if not event.verify_signature():
            # Invalid seals can never be made valid merely by recomputing the chain.
            chain.append("INVALID_EVENT_SIGNATURE")
            previous = chain[-1]
            continue
        previous = hash_event(event, previous)
        chain.append(previous)
    return tuple(chain)


def verify_hash_chain(
    events: list[InvestigationEvent],
    chain: tuple[str, ...],
) -> bool:
    if len(events) != len(chain):
        return False
    if not all(event.verify_signature() for event in events):
        return False
    return build_hash_chain(events) == chain
