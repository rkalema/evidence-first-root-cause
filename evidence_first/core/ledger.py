from __future__ import annotations

from dataclasses import dataclass, field

from .models import Claim, EvidenceRecord


@dataclass
class EvidenceLedger:
    _evidence: dict[str, EvidenceRecord] = field(default_factory=dict)
    _claims: dict[str, Claim] = field(default_factory=dict)

    def add_evidence(self, record: EvidenceRecord) -> None:
        if record.evidence_id in self._evidence:
            raise ValueError(f"evidence id already exists: {record.evidence_id}")
        self._evidence[record.evidence_id] = record

    def add_claim(self, claim: Claim) -> None:
        if claim.claim_id in self._claims:
            raise ValueError(f"claim id already exists: {claim.claim_id}")
        missing = [eid for eid in claim.evidence_ids if eid not in self._evidence]
        if missing:
            raise ValueError(f"claim cites unknown evidence ids: {missing}")
        self._claims[claim.claim_id] = claim

    def evidence(self, evidence_id: str) -> EvidenceRecord:
        return self._evidence[evidence_id]

    def claim(self, claim_id: str) -> Claim:
        return self._claims[claim_id]

    @property
    def evidence_records(self) -> tuple[EvidenceRecord, ...]:
        return tuple(self._evidence.values())

    @property
    def claims(self) -> tuple[Claim, ...]:
        return tuple(self._claims.values())
