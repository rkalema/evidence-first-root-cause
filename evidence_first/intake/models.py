from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from evidence_first.core.models import _deep_freeze


class IssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    source_type: str
    fingerprint: str
    byte_size: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntakeIssue:
    code: str
    message: str
    severity: IssueSeverity
    field: str | None = None


@dataclass(frozen=True)
class IntakeRecord:
    record_id: str
    source_id: str
    payload: dict[str, Any]
    row_number: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", _deep_freeze(self.payload))


@dataclass(frozen=True)
class IntakeResult:
    source: SourceDescriptor
    records: tuple[IntakeRecord, ...]
    issues: tuple[IntakeIssue, ...]
    valid: bool
    stats: dict[str, Any]

    @property
    def blocking_issues(self) -> tuple[IntakeIssue, ...]:
        return tuple(i for i in self.issues if i.severity is IssueSeverity.ERROR)
