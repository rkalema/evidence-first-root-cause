from __future__ import annotations

from dataclasses import dataclass, field

from .hypotheses import HypothesisRegistry
from .ledger import EvidenceLedger
from .models import InvestigationStatus


@dataclass
class InvestigationState:
    question: str
    ledger: EvidenceLedger = field(default_factory=EvidenceLedger)
    hypotheses: HypothesisRegistry = field(default_factory=HypothesisRegistry)
    unknowns: list[str] = field(default_factory=list)
    status: InvestigationStatus = InvestigationStatus.OPEN
    signal_validated: bool = False
    minimum_competing_hypotheses: int = 2

    def __post_init__(self) -> None:
        self.hypotheses.ledger = self.ledger

    def mark_signal_validated(self, trustworthy: bool) -> None:
        self.signal_validated = bool(trustworthy)
        if not trustworthy:
            self.status = InvestigationStatus.INSUFFICIENT_EVIDENCE

    def mark_data_quality_blocked(self, reason: str) -> None:
        self.status = InvestigationStatus.DATA_QUALITY_BLOCKED
        if reason not in self.unknowns:
            self.unknowns.append(reason)

    def mark_insufficient_evidence(self, reason: str) -> None:
        self.status = InvestigationStatus.INSUFFICIENT_EVIDENCE
        if reason not in self.unknowns:
            self.unknowns.append(reason)
