from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any

from evidence_first.core.models import _deep_freeze


class IssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class _FrozenPayload(dict):
    def __setitem__(self, key, value):
        return None
    def __delitem__(self, key):
        return None
    def clear(self):
        return None
    def pop(self, *args, **kwargs):
        return None
    def popitem(self):
        return None
    def setdefault(self, key, default=None):
        return self.get(key, default)
    def update(self, *args, **kwargs):
        return None


def _freeze_payload(value: Any) -> Any:
    if isinstance(value, dict):
        out = _FrozenPayload()
        for key, item in value.items():
            dict.__setitem__(out, str(key), _freeze_payload(item))
        return out
    if isinstance(value, list):
        return tuple(_freeze_payload(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_payload(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_payload(item) for item in value)
    return value


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    source_type: str
    fingerprint: str
    byte_size: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _deep_freeze(self.metadata))


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
        object.__setattr__(self, "payload", _freeze_payload(self.payload))


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
