from __future__ import annotations

import csv
import io
import json
from collections import Counter
from typing import Any

from .fingerprint import fingerprint_bytes
from .models import IntakeIssue, IntakeRecord, IntakeResult, IssueSeverity, SourceDescriptor


def _make_source(source_id: str, source_type: str, raw: bytes, metadata: dict[str, Any] | None = None) -> SourceDescriptor:
    if not source_id.strip():
        raise ValueError("source_id cannot be empty")
    return SourceDescriptor(
        source_id=source_id,
        source_type=source_type,
        fingerprint=fingerprint_bytes(raw),
        byte_size=len(raw),
        metadata=metadata or {},
    )


def _valid(issues: list[IntakeIssue]) -> bool:
    return not any(issue.severity is IssueSeverity.ERROR for issue in issues)


def ingest_text(text: str, *, source_id: str, metadata: dict[str, Any] | None = None) -> IntakeResult:
    raw = text.encode("utf-8")
    source = _make_source(source_id, "text", raw, metadata)
    issues: list[IntakeIssue] = []

    normalized = text.strip()
    if not normalized:
        issues.append(IntakeIssue("empty_source", "Text source contains no non-whitespace content.", IssueSeverity.ERROR))
        records: tuple[IntakeRecord, ...] = ()
    else:
        records = (IntakeRecord("r1", source_id, {"text": normalized}, 1),)

    return IntakeResult(source, records, tuple(issues), _valid(issues), {"record_count": len(records)})


def ingest_json(text: str, *, source_id: str, metadata: dict[str, Any] | None = None) -> IntakeResult:
    raw = text.encode("utf-8")
    source = _make_source(source_id, "json", raw, metadata)
    issues: list[IntakeIssue] = []
    records: list[IntakeRecord] = []

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        issues.append(IntakeIssue("invalid_json", f"JSON parse error at line {exc.lineno}, column {exc.colno}.", IssueSeverity.ERROR))
        return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})

    items: list[Any]
    if isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict):
        items = [parsed]
    else:
        issues.append(IntakeIssue("unsupported_json_root", "JSON root must be an object or array of objects.", IssueSeverity.ERROR))
        return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})

    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            issues.append(IntakeIssue("non_object_record", f"JSON item {idx} is not an object.", IssueSeverity.ERROR))
            continue
        records.append(IntakeRecord(f"r{idx}", source_id, item, idx))

    return IntakeResult(source, tuple(records), tuple(issues), _valid(issues), {"record_count": len(records)})


def ingest_csv(text: str, *, source_id: str, metadata: dict[str, Any] | None = None) -> IntakeResult:
    raw = text.encode("utf-8")
    source = _make_source(source_id, "csv", raw, metadata)
    issues: list[IntakeIssue] = []

    stream = io.StringIO(text)
    reader = csv.DictReader(stream)
    if not reader.fieldnames:
        issues.append(IntakeIssue("missing_header", "CSV has no header row.", IssueSeverity.ERROR))
        return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})

    normalized_headers = [h.strip() if h is not None else "" for h in reader.fieldnames]
    if any(not h for h in normalized_headers):
        issues.append(IntakeIssue("blank_header", "CSV contains a blank column header.", IssueSeverity.ERROR))
    counts = Counter(normalized_headers)
    duplicates = sorted(h for h, count in counts.items() if h and count > 1)
    if duplicates:
        issues.append(IntakeIssue("duplicate_headers", f"CSV contains duplicate headers: {', '.join(duplicates)}.", IssueSeverity.ERROR))

    records: list[IntakeRecord] = []
    blank_cells = 0
    total_cells = 0
    seen_payloads: set[tuple[tuple[str, str], ...]] = set()
    duplicate_rows = 0

    for row_number, row in enumerate(reader, start=2):
        payload: dict[str, str] = {}
        for header, value in row.items():
            if header is None:
                continue
            key = header.strip()
            val = "" if value is None else value.strip()
            payload[key] = val
            total_cells += 1
            if val == "":
                blank_cells += 1

        signature = tuple(sorted(payload.items()))
        if signature in seen_payloads:
            duplicate_rows += 1
        else:
            seen_payloads.add(signature)
        records.append(IntakeRecord(f"r{len(records)+1}", source_id, payload, row_number))

    if not records:
        issues.append(IntakeIssue("no_data_rows", "CSV contains headers but no data rows.", IssueSeverity.ERROR))
    if duplicate_rows:
        issues.append(IntakeIssue("duplicate_rows", f"Detected {duplicate_rows} duplicate data row(s).", IssueSeverity.WARNING))

    missing_rate = (blank_cells / total_cells) if total_cells else 0.0
    if missing_rate > 0:
        issues.append(IntakeIssue("missing_values", f"Blank-cell rate is {missing_rate:.1%}.", IssueSeverity.WARNING))

    stats = {
        "record_count": len(records),
        "column_count": len(normalized_headers),
        "missing_cell_rate": round(missing_rate, 6),
        "duplicate_row_count": duplicate_rows,
        "headers": normalized_headers,
    }
    return IntakeResult(source, tuple(records), tuple(issues), _valid(issues), stats)
