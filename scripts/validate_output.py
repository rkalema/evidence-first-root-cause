#!/usr/bin/env python3
"""Validate an Evidence-First result against the canonical schema and invariants."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "root_cause_output.schema.json"


def _reject_constant(value: str):
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, parse_constant=_reject_constant)


def _nonfinite_paths(value: Any, path: str = "<root>") -> list[str]:
    errors: list[str] = []
    if isinstance(value, float) and not math.isfinite(value):
        errors.append(f"{path}: non-finite numbers are not allowed")
    elif isinstance(value, dict):
        for key, item in value.items():
            child = str(key) if path == "<root>" else f"{path}.{key}"
            errors.extend(_nonfinite_paths(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_nonfinite_paths(item, f"{path}[{index}]"))
    return errors


def validate_document(document: dict) -> list[str]:
    if not isinstance(document, dict):
        return ["<root>: document must be an object"]

    errors_out = _nonfinite_paths(document)
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: list(error.path),
    )
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        errors_out.append(f"{location}: {error.message}")
    return errors_out


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
    except (OSError, json.JSONDecodeError, ValueError) as exc:
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
