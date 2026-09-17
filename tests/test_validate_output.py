from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_output import validate_document


FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> dict:
    with (FIXTURES / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_supported_case_is_valid() -> None:
    errors = validate_document(read_fixture("valid_supported.json"))
    assert errors == []


def test_insufficient_evidence_case_is_valid() -> None:
    errors = validate_document(read_fixture("valid_insufficient.json"))
    assert errors == []


def test_missing_evidence_is_rejected() -> None:
    errors = validate_document(read_fixture("invalid_missing_evidence.json"))
    assert errors
    assert any("evidence" in error for error in errors)
