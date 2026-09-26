from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


_EVENT_KEY = os.environ.get("EFRC_AUDIT_HMAC_KEY", "").encode("utf-8") or os.urandom(32)


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
    raise TypeError(f"unsupported audit metadata type: {type(value).__name__}")


def _event_payload(event: "InvestigationEvent") -> bytes:
    data = {
        "event_type": event.event_type,
        "stage": event.stage,
        "message": event.message,
        "actor": event.actor,
        "metadata": _canonical(event.metadata),
        "timestamp": event.timestamp,
    }
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class InvestigationEvent:
    event_type: str
    stage: str
    message: str
    actor: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str | None = None
    signature: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        timestamp = self.timestamp
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        else:
            # Reject caller-supplied real timestamps. Short synthetic labels such as
            # "t1" remain useful in deterministic unit tests.
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
            else:
                timestamp = datetime.now(timezone.utc).isoformat()
        object.__setattr__(self, "timestamp", timestamp)

        if self.signature is None:
            sig = hmac.new(_EVENT_KEY, _event_payload(self), hashlib.sha256).hexdigest()
            object.__setattr__(self, "signature", sig)

    def verify_signature(self) -> bool:
        expected = hmac.new(_EVENT_KEY, _event_payload(self), hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature or "", expected)
