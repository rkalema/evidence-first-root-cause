#!/usr/bin/env python3
"""Validate an evidence-first-root-cause JSON result against the canonical schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "root_cause_output.schema.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_document(document: dict) -> list[str]:
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))

    formatted: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        formatted.append(f"{location}: {error.message}")
    return formatted


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_output.py <result.json>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2

    try:
        document = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Unable to read JSON: {exc}")
        return 2

    errors = validate_document(document)
    if errors:
        print("INVALID")
        for item in errors:
            print(f"- {item}")
        return 1

    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
