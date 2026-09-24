from __future__ import annotations

from dataclasses import dataclass, field

from .models import Hypothesis


@dataclass
class HypothesisRegistry:
    _items: dict[str, Hypothesis] = field(default_factory=dict)

    def add(self, hypothesis: Hypothesis) -> None:
        if hypothesis.hypothesis_id in self._items:
            raise ValueError(f"hypothesis id already exists: {hypothesis.hypothesis_id}")
        self._items[hypothesis.hypothesis_id] = hypothesis

    def support(self, hypothesis_id: str, evidence_id: str) -> None:
        h = self._items[hypothesis_id]
        if evidence_id not in h.supporting_evidence_ids:
            h.supporting_evidence_ids.append(evidence_id)
        h.evaluate()

    def contradict(self, hypothesis_id: str, evidence_id: str) -> None:
        h = self._items[hypothesis_id]
        if evidence_id not in h.contradicting_evidence_ids:
            h.contradicting_evidence_ids.append(evidence_id)
        h.evaluate()

    def get(self, hypothesis_id: str) -> Hypothesis:
        return self._items[hypothesis_id]

    @property
    def all(self) -> tuple[Hypothesis, ...]:
        return tuple(self._items.values())
