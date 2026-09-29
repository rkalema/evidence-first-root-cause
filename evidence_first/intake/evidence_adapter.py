from __future__ import annotations

from .models import IntakeResult


def to_evidence_payloads(result: IntakeResult) -> list[dict[str, object]]:
    """Convert intake records into provenance-preserving evidence candidates.

    This intentionally does not label raw rows as conclusions. Downstream evidence
    normalization decides which fields become observations or metrics.
    """
    payloads: list[dict[str, object]] = []
    for record in result.records:
        payloads.append(
            {
                "source_id": result.source.source_id,
                "source_fingerprint": result.source.fingerprint,
                "record_id": record.record_id,
                "row_number": record.row_number,
                "payload": record.payload,
            }
        )
    return payloads
