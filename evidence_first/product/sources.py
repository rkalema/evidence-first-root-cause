from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from evidence_first.core.models import EvidenceKind, EvidenceRecord
from evidence_first.intake import ingest_csv, ingest_json, ingest_text, ingest_xlsx_bytes
from evidence_first.runtime import ToolExecutionBroker
from evidence_first.tools.multisource import multisource_dataframe_registry

MAX_CONTEXT_RECORDS_PER_SOURCE = 50
MAX_TEXT_CONTEXT_CHARS = 20_000


@dataclass(frozen=True)
class PreparedSources:
    source_inventory: tuple[dict[str, Any], ...]
    evidence_records: tuple[EvidenceRecord, ...]
    frames: dict[str, pd.DataFrame]
    tool_broker: ToolExecutionBroker | None


def _read_text_bytes(path: Path) -> tuple[bytes, str]:
    raw = path.read_bytes()
    try:
        return raw, raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path.name}: source is not valid UTF-8 text") from exc


def _intake(path: Path):
    ext = path.suffix.lower()
    if ext in {".xlsx", ".xlsm"}:
        return ingest_xlsx_bytes(path.read_bytes(), source_id=path.name)
    raw, text = _read_text_bytes(path)
    if ext == ".csv":
        return ingest_csv(text, source_id=path.name, raw_bytes=raw)
    if ext == ".json":
        return ingest_json(text, source_id=path.name, raw_bytes=raw)
    return ingest_text(text, source_id=path.name, raw_bytes=raw)


def _frame_from_records(records) -> pd.DataFrame:
    return pd.DataFrame([dict(record.payload) for record in records])


def _source_summary_evidence(result) -> EvidenceRecord:
    issues = [
        {
            "code": issue.code,
            "severity": issue.severity.value,
            "field": issue.field,
        }
        for issue in result.issues
    ]
    statement = (
        f"Source {result.source.source_id} ingested with "
        f"{result.stats.get('record_count', len(result.records))} record(s); "
        f"valid={result.valid}."
    )
    return EvidenceRecord(
        evidence_id=f"source:{result.source.fingerprint.split(':',1)[1][:20]}",
        statement=statement,
        kind=EvidenceKind.DOCUMENT,
        source=result.source.source_id,
        reliability=1.0 if result.valid else 0.0,
        metadata={
            "fingerprint": result.source.fingerprint,
            "source_type": result.source.source_type,
            "stats": result.stats,
            "issues": issues,
        },
    )


def _record_evidence(result) -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []
    for index, record in enumerate(
        result.records[:MAX_CONTEXT_RECORDS_PER_SOURCE],
        start=1,
    ):
        payload = dict(record.payload)
        if result.source.source_type == "text":
            text = str(payload.get("text", ""))[:MAX_TEXT_CONTEXT_CHARS]
            payload = {"text": text}
        statement = json.dumps(payload, sort_keys=True, default=str)
        records.append(
            EvidenceRecord(
                evidence_id=(
                    f"{result.source.source_id}:r{index}:"
                    f"{result.source.fingerprint.split(':',1)[1][:12]}"
                ),
                statement=statement,
                kind=EvidenceKind.OBSERVATION,
                source=result.source.source_id,
                reliability=1.0 if result.valid else 0.0,
                metadata={
                    "source_fingerprint": result.source.fingerprint,
                    "record_id": record.record_id,
                    "row_number": record.row_number,
                },
            )
        )
    return records


def prepare_sources(paths: list[Path]) -> PreparedSources:
    if not paths:
        raise ValueError("at least one evidence source is required")

    seen_names: set[str] = set()
    inventory: list[dict[str, Any]] = []
    evidence: list[EvidenceRecord] = []
    frames: dict[str, pd.DataFrame] = {}

    for raw_path in paths:
        path = raw_path.expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(path)
        if path.name in seen_names:
            raise ValueError(
                f"duplicate source filename {path.name!r}; source IDs must be unique"
            )
        seen_names.add(path.name)

        result = _intake(path)
        inventory.append(
            {
                "source_id": result.source.source_id,
                "source_type": result.source.source_type,
                "fingerprint": result.source.fingerprint,
                "byte_size": result.source.byte_size,
                "valid": result.valid,
                "stats": result.stats,
                "issues": [
                    {
                        "code": issue.code,
                        "message": issue.message,
                        "severity": issue.severity.value,
                        "field": issue.field,
                    }
                    for issue in result.issues
                ],
                "sample": [
                    {
                        "record_id": record.record_id,
                        "row_number": record.row_number,
                        "payload": {
                            str(key): value
                            for key, value in dict(record.payload).items()
                        },
                    }
                    for record in result.records[:5]
                ],
            }
        )

        evidence.append(_source_summary_evidence(result))
        evidence.extend(_record_evidence(result))

        if (
            result.valid
            and result.source.source_type in {"csv", "xlsx"}
            and result.records
        ):
            frames[result.source.source_id] = _frame_from_records(result.records)

    invalid = [item["source_id"] for item in inventory if not item["valid"]]
    if invalid:
        raise ValueError(
            "blocking intake issues in source(s): " + ", ".join(invalid)
        )

    broker = None
    if frames:
        registry = multisource_dataframe_registry(frames)
        trusted_ids = {
            record.evidence_id for record in evidence
        } | {
            item["fingerprint"] for item in inventory
        } | {
            item["source_id"] for item in inventory
        }
        broker = ToolExecutionBroker(
            registry,
            trusted_source_ids=trusted_ids,
        )

    return PreparedSources(
        source_inventory=tuple(inventory),
        evidence_records=tuple(evidence),
        frames=frames,
        tool_broker=broker,
    )
