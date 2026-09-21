from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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

    def __post_init__(self) -> None:
        if not 0 <= self.reliability <= 1:
            raise ValueError("reliability must be between 0 and 1")
        if not self.statement.strip():
            raise ValueError("evidence statement cannot be empty")
        if not self.source.strip():
            raise ValueError("evidence source cannot be empty")


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

    def evaluate(self) -> HypothesisStatus:
        support = len(self.supporting_evidence_ids)
        contradiction = len(self.contradicting_evidence_ids)
        if support == 0 and contradiction > 0:
            self.status = HypothesisStatus.NOT_SUPPORTED
        elif support > 0 and contradiction == 0:
            self.status = HypothesisStatus.SUPPORTED
        elif support > 0 and contradiction > 0:
            self.status = HypothesisStatus.PARTIALLY_SUPPORTED
        else:
            self.status = HypothesisStatus.UNTESTED
        return self.status
