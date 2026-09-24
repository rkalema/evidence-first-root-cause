from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .models import Hypothesis

if TYPE_CHECKING:
    from .ledger import EvidenceLedger


@dataclass
class HypothesisRegistry:
    _items: dict[str, Hypothesis] = field(default_factory=dict)
    ledger: "EvidenceLedger | None" = field(default=None, repr=False)
    invalid_evidence_refs: list[tuple[str, str]] = field(default_factory=list)

    def add(self, hypothesis: Hypothesis) -> None:
        if hypothesis.hypothesis_id in self._items:
            raise ValueError(f"hypothesis id already exists: {hypothesis.hypothesis_id}")
        self._items[hypothesis.hypothesis_id] = hypothesis

    def _resolve(self, hypothesis_id: str, evidence_id: str):
        if hypothesis_id not in self._items:
            raise KeyError(hypothesis_id)
        if self.ledger is None:
            return None
        try:
            record = self.ledger.evidence(evidence_id)
        except KeyError:
            self.invalid_evidence_refs.append((hypothesis_id, evidence_id))
            return None
        if not record.verify_integrity():
            self.invalid_evidence_refs.append((hypothesis_id, evidence_id))
            return None
        return record

    def support(self, hypothesis_id: str, evidence_id: str) -> bool:
        h = self._items[hypothesis_id]
        if evidence_id in h.contradicting_evidence_ids:
            raise ValueError("same evidence cannot both support and contradict one hypothesis")
        record = self._resolve(hypothesis_id, evidence_id)
        if self.ledger is not None and record is None:
            return False
        if evidence_id not in h.supporting_evidence_ids:
            h.supporting_evidence_ids.append(evidence_id)
        self.evaluate(hypothesis_id)
        return True

    def contradict(self, hypothesis_id: str, evidence_id: str) -> bool:
        h = self._items[hypothesis_id]
        if evidence_id in h.supporting_evidence_ids:
            raise ValueError("same evidence cannot both support and contradict one hypothesis")
        record = self._resolve(hypothesis_id, evidence_id)
        if self.ledger is not None and record is None:
            return False
        if evidence_id not in h.contradicting_evidence_ids:
            h.contradicting_evidence_ids.append(evidence_id)
        self.evaluate(hypothesis_id)
        return True

    def _weights(self, hypothesis: Hypothesis) -> tuple[float, float]:
        if self.ledger is None:
            return float(len(hypothesis.supporting_evidence_ids)), float(
                len(hypothesis.contradicting_evidence_ids)
            )

        support = 0.0
        contradiction = 0.0
        for evidence_id in hypothesis.supporting_evidence_ids:
            try:
                record = self.ledger.evidence(evidence_id)
            except KeyError:
                continue
            if record.verify_integrity():
                support += max(0.0, record.reliability)
        for evidence_id in hypothesis.contradicting_evidence_ids:
            try:
                record = self.ledger.evidence(evidence_id)
            except KeyError:
                continue
            if record.verify_integrity():
                contradiction += max(0.0, record.reliability)
        return support, contradiction

    def evaluate(self, hypothesis_id: str):
        h = self._items[hypothesis_id]
        support, contradiction = self._weights(h)
        return h.evaluate(support, contradiction)

    def get(self, hypothesis_id: str) -> Hypothesis:
        return self._items[hypothesis_id]

    @property
    def all(self) -> tuple[Hypothesis, ...]:
        return tuple(self._items.values())
