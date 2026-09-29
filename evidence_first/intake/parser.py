from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter
from typing import Any

from .fingerprint import fingerprint_bytes
from .models import IntakeIssue, IntakeRecord, IntakeResult, IssueSeverity, SourceDescriptor

MAX_TEXT_BYTES = 10 * 1024 * 1024
MAX_CSV_ROWS = 250_000
MAX_FIELD_CHARS = 100_000
NULL_TOKENS = {"", "nan", "n/a", "na", "null", "none", "-"}
FORMULA_PREFIXES = ("=", "+", "-", "@")
INSTRUCTION_RE = re.compile(
    r"(ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions|"
    r"\bsystem\s*:|\boperator\s+note\b|"
    r"declare\s+root[_ -]?cause|root_cause_supported)",
    re.IGNORECASE,
)


class DuplicateJSONKey(ValueError):
    pass


def _make_source(
    source_id: str,
    source_type: str,
    raw: bytes,
    metadata: dict[str, Any] | None = None,
) -> SourceDescriptor:
    if not isinstance(source_id, str) or not source_id.strip():
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


def _flag_cell(
    value: str,
    issues: list[IntakeIssue],
    *,
    field: str | None = None,
) -> None:
    if "\x00" in value or any(ord(ch) < 32 and ch not in "\t\r\n" for ch in value):
        issues.append(
            IntakeIssue(
                "control_character",
                "Cell contains a NUL or unsupported control character.",
                IssueSeverity.WARNING,
                field,
            )
        )
    stripped = value.lstrip()
    if stripped and stripped[0] in FORMULA_PREFIXES and stripped.lower() not in NULL_TOKENS:
        issues.append(
            IntakeIssue(
                "formula_like",
                "Cell begins with a spreadsheet formula/DDE prefix.",
                IssueSeverity.WARNING,
                field,
            )
        )
    if INSTRUCTION_RE.search(value):
        issues.append(
            IntakeIssue(
                "instruction_like",
                "Cell contains instruction-like text; treat as untrusted evidence data.",
                IssueSeverity.WARNING,
                field,
            )
        )


def ingest_text(
    text: str,
    *,
    source_id: str,
    metadata: dict[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> IntakeResult:
    raw = raw_bytes if raw_bytes is not None else text.encode("utf-8")
    source = _make_source(source_id, "text", raw, metadata)
    issues: list[IntakeIssue] = []
    if len(raw) > MAX_TEXT_BYTES:
        issues.append(IntakeIssue("source_too_large", "Text source exceeds size limit.", IssueSeverity.ERROR))

    normalized = text.strip()
    if not normalized:
        issues.append(IntakeIssue("empty_source", "Text source contains no non-whitespace content.", IssueSeverity.ERROR))
        records: tuple[IntakeRecord, ...] = ()
    else:
        _flag_cell(normalized, issues, field="text")
        records = (IntakeRecord("r1", source_id, {"text": normalized}, 1),)

    return IntakeResult(source, records, tuple(issues), _valid(issues), {"record_count": len(records)})


def _pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str):
    raise ValueError(f"non-standard JSON number: {value}")


def ingest_json(
    text: str,
    *,
    source_id: str,
    metadata: dict[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> IntakeResult:
    raw = raw_bytes if raw_bytes is not None else text.encode("utf-8")
    source = _make_source(source_id, "json", raw, metadata)
    issues: list[IntakeIssue] = []
    records: list[IntakeRecord] = []

    if len(raw) > MAX_TEXT_BYTES:
        issues.append(IntakeIssue("source_too_large", "JSON source exceeds size limit.", IssueSeverity.ERROR))
        return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})

    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except DuplicateJSONKey as exc:
        issues.append(IntakeIssue("duplicate_json_key", str(exc), IssueSeverity.ERROR))
        return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        issues.append(IntakeIssue("invalid_json", f"JSON parse error: {exc}", IssueSeverity.ERROR))
        return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})

    if isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict):
        items = [parsed]
    else:
        issues.append(IntakeIssue("unsupported_json_root", "JSON root must be an object or array of objects.", IssueSeverity.ERROR))
        return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})

    if len(items) > MAX_CSV_ROWS:
        issues.append(IntakeIssue("too_many_records", "JSON record count exceeds limit.", IssueSeverity.ERROR))
        return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})

    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            issues.append(IntakeIssue("non_object_record", f"JSON item {idx} is not an object.", IssueSeverity.ERROR))
            continue
        records.append(IntakeRecord(f"r{idx}", source_id, item, idx))

    return IntakeResult(source, tuple(records), tuple(issues), _valid(issues), {"record_count": len(records)})


def ingest_csv(
    text: str,
    *,
    source_id: str,
    metadata: dict[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> IntakeResult:
    raw = raw_bytes if raw_bytes is not None else text.encode("utf-8")
    source = _make_source(source_id, "csv", raw, metadata)
    issues: list[IntakeIssue] = []

    if len(raw) > MAX_TEXT_BYTES:
        issues.append(IntakeIssue("source_too_large", "CSV source exceeds size limit.", IssueSeverity.ERROR))
        return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})

    if any(len(line) > MAX_FIELD_CHARS for line in text.splitlines()):
        issues.append(IntakeIssue("field_too_large", "CSV contains a field/line exceeding the configured limit.", IssueSeverity.ERROR))
        return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})

    stream = io.StringIO(text)
    try:
        reader = csv.DictReader(
            stream,
            restkey="__extra_columns__",
            restval=None,
            strict=True,
        )
        if not reader.fieldnames:
            issues.append(IntakeIssue("missing_header", "CSV has no header row.", IssueSeverity.ERROR))
            return IntakeResult(source, (), tuple(issues), False, {"record_count": 0})

        normalized_headers = [
            (h or "").lstrip("\ufeff").strip()
            for h in reader.fieldnames
        ]
        if any(not h for h in normalized_headers):
            issues.append(IntakeIssue("blank_header", "CSV contains a blank column header.", IssueSeverity.ERROR))
        counts = Counter(normalized_headers)
        duplicates = sorted(h for h, count in counts.items() if h and count > 1)
        if duplicates:
            issues.append(IntakeIssue("duplicate_headers", f"CSV contains duplicate headers: {', '.join(duplicates)}.", IssueSeverity.ERROR))

        records: list[IntakeRecord] = []
        missing_cells = 0
        total_cells = 0
        seen_payloads: set[tuple[tuple[str, str], ...]] = set()
        duplicate_rows = 0

        for row_number, row in enumerate(reader, start=2):
            if len(records) >= MAX_CSV_ROWS:
                issues.append(IntakeIssue("too_many_records", "CSV row count exceeds limit.", IssueSeverity.ERROR))
                break

            extras = row.pop("__extra_columns__", None)
            if extras:
                issues.append(
                    IntakeIssue(
                        "ragged_extra_columns",
                        f"Row {row_number} contains extra columns.",
                        IssueSeverity.ERROR,
                    )
                )

            payload: dict[str, str] = {}
            for raw_header, value in row.items():
                key = (raw_header or "").lstrip("\ufeff").strip()
                if value is None:
                    issues.append(
                        IntakeIssue(
                            "ragged_missing_columns",
                            f"Row {row_number} is missing one or more columns.",
                            IssueSeverity.ERROR,
                            key or None,
                        )
                    )
                    val = ""
                else:
                    val = value.strip()
                payload[key] = val
                total_cells += 1
                if val.lower() in NULL_TOKENS:
                    missing_cells += 1
                _flag_cell(val, issues, field=key)

            signature = tuple(sorted(payload.items()))
            if signature in seen_payloads:
                duplicate_rows += 1
            else:
                seen_payloads.add(signature)
            records.append(
                IntakeRecord(f"r{len(records)+1}", source_id, payload, row_number)
            )

    except csv.Error as exc:
        issues.append(IntakeIssue("invalid_csv", f"CSV parse error: {exc}", IssueSeverity.ERROR))
        records = []
        normalized_headers = []
        duplicate_rows = 0
        missing_cells = 0
        total_cells = 0

    if not records:
        issues.append(IntakeIssue("no_data_rows", "CSV contains no valid data rows.", IssueSeverity.ERROR))
    if duplicate_rows:
        issues.append(IntakeIssue("duplicate_rows", f"Detected {duplicate_rows} duplicate data row(s).", IssueSeverity.WARNING))

    missing_rate = (missing_cells / total_cells) if total_cells else 0.0
    if missing_rate > 0:
        issues.append(IntakeIssue("missing_values", f"Missing/null-token cell rate is {missing_rate:.1%}.", IssueSeverity.WARNING))

    stats = {
        "record_count": len(records),
        "column_count": len(normalized_headers),
        "missing_cell_rate": round(missing_rate, 6),
        "duplicate_row_count": duplicate_rows,
        "headers": normalized_headers,
    }
    return IntakeResult(source, tuple(records), tuple(issues), _valid(issues), stats)
