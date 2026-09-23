from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass(frozen=True)
class InvestigationEvent:
    event_type: str
    stage: str
    message: str
    actor: str
    metadata: dict[str, Any]=field(default_factory=dict)
    timestamp: str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
