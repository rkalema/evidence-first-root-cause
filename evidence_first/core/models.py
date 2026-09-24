from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class _ImmutableDict(dict):
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


class _ImmutableByteArray(bytearray):
    def __setitem__(self, key, value):
        return None
    def __delitem__(self, key):
        return None
    def append(self, value):
        return None
    def extend(self, value):
        return None
    def insert(self, index, value):
        return None
    def pop(self, index=-1):
        return None
    def remove(self, value):
        return None
    def reverse(self):
        return None


class _ReadOnlyObjectProxy:
    __slots__ = ("_values",)

    def __init__(self, value: Any):
        copied = copy.deepcopy(getattr(value, "__dict__", {}))
        object.__setattr__(
            self,
            "_values",
            {str(k): _deep_freeze(v) for k, v in copied.items()},
        )

    def __getattr__(self, name: str) -> Any:
        values = object.__getattribute__(self, "_values")
        if name not in values:
            raise AttributeError(name)
        return values[name]

    def __setattr__(self, name: str, value: Any) -> None:
        return None

    def __repr__(self) -> str:
        return f"ReadOnlyObjectProxy({object.__getattribute__(self, '_values')!r})"


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, _ImmutableDict):
        return value
    if isinstance(value, dict):
        result = _ImmutableDict()
        for key, item in value.items():
            dict.__setitem__(result, str(key), _deep_freeze(item))
        return result
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_deep_freeze(item) for item in value)
    if isinstance(value, bytearray):
        return _ImmutableByteArray(value)
    if isinstance(value, (str, int, bool, type(None), bytes)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite values are not allowed in immutable evidence")
        return value
    return _ReadOnlyObjectProxy(value)


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True))
    if isinstance(value, (_ImmutableByteArray, bytearray, bytes)):
        return {"__type__": "bytes", "hex": bytes(value).hex()}
    if isinstance(value, _ReadOnlyObjectProxy):
        return {"__type__": "object", "values": _canonical(object.__getattribute__(value, "_values"))}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite values cannot be canonicalized")
        return {"__type__": "float", "value": repr(value)}
    if isinstance(value, (str, int, bool)) or value is None:
        return {"__type__": type(value).__name__, "value": value}
    raise TypeError(f"unsupported canonical value type: {type(value).__name__}")


class EvidenceKind(str, Enum):
    OBSERVATION = "observation"
    TOOL_OUTPUT = "tool_output"
    HUMAN_ASSERTION = "human_assertion"
    DOCUMENT = "document"
    METRIC = "metric"


class ClaimClass(str, Enum):
    OBSERVATION = "observation"
    INFERENCE = "inference"
    CONCLUSION = "conclusion"
    UNKNOWN = "unknown"


class HypothesisStatus(str, Enum):
    UNTESTED = "untested"
    PARTIALLY_SUPPORTED = "partially_supported"
    SUPPORTED = "supported"
    NOT_SUPPORTED = "not_supported"


class InvestigationStatus(str, Enum):
    OPEN = "open"
    ROOT_CAUSE_SUPPORTED = "root_cause_supported"
    MULTIPLE_CONTRIBUTORS_SUPPORTED = "multiple_contributors_supported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    DATA_QUALITY_BLOCKED = "data_quality_blocked"


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    statement: str
    kind: EvidenceKind
    source: str
    reliability: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    content_hash: str = field(init=False)
    _sealed_statement: str = field(init=False, repr=False, compare=False)

    def __getattribute__(self, name: str) -> Any:
        if name == "statement":
            try:
                return object.__getattribute__(self, "_sealed_statement")
            except AttributeError:
                return object.__getattribute__(self, "__dict__").get("statement", "")
        return object.__getattribute__(self, name)

    def __post_init__(self) -> None:
        raw_statement = object.__getattribute__(self, "__dict__").get("statement", "")
        if not 0 <= self.reliability <= 1:
            raise ValueError("reliability must be between 0 and 1")
        if not isinstance(raw_statement, str) or not raw_statement.strip():
            raise ValueError("evidence statement cannot be empty")
        if not self.source.strip():
            raise ValueError("evidence source cannot be empty")
        frozen = _deep_freeze(self.metadata)
        object.__setattr__(self, "metadata", frozen)
        object.__setattr__(self, "_sealed_statement", raw_statement)
        payload = {
            "evidence_id": self.evidence_id,
            "statement": raw_statement,
            "kind": self.kind.value,
            "source": self.source,
            "reliability": self.reliability,
            "metadata": _canonical(frozen),
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        object.__setattr__(self, "content_hash", digest)

    def verify_integrity(self) -> bool:
        payload = {
            "evidence_id": self.evidence_id,
            "statement": self.statement,
            "kind": self.kind.value,
            "source": self.source,
            "reliability": self.reliability,
            "metadata": _canonical(self.metadata),
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return digest == self.content_hash


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    classification: ClaimClass
    evidence_ids: tuple[str, ...] = ()
    confidence: str | None = None

    def __post_init__(self) -> None:
        if self.classification is not ClaimClass.UNKNOWN and not self.evidence_ids:
            raise ValueError("non-unknown claims must cite evidence")


@dataclass
class Hypothesis:
    hypothesis_id: str
    statement: str
    mechanism: str
    expected_evidence: list[str] = field(default_factory=list)
    disconfirming_evidence: list[str] = field(default_factory=list)
    supporting_evidence_ids: list[str] = field(default_factory=list)
    contradicting_evidence_ids: list[str] = field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.UNTESTED
    relationship: str = "competing"

    def __post_init__(self) -> None:
        if self.relationship not in {"competing", "additive"}:
            raise ValueError("relationship must be 'competing' or 'additive'")

    def evaluate(self, support_weight: float | None = None, contradiction_weight: float | None = None) -> HypothesisStatus:
        support = float(len(self.supporting_evidence_ids)) if support_weight is None else support_weight
        contradiction = float(len(self.contradicting_evidence_ids)) if contradiction_weight is None else contradiction_weight
        if support <= 0 and contradiction > 0:
            self.status = HypothesisStatus.NOT_SUPPORTED
        elif support > contradiction and support > 0:
            self.status = HypothesisStatus.SUPPORTED
        elif support > 0 and contradiction > 0:
            self.status = HypothesisStatus.PARTIALLY_SUPPORTED
        else:
            self.status = HypothesisStatus.UNTESTED
        return self.status
