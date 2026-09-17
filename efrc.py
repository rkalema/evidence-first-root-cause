#!/usr/bin/env python3
"""CLI for Evidence-First Root Cause."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.evaluate_case import score
from scripts.validate_output import validate_document


ROOT = Path(__file__).resolve().parent
CASES_DIR = ROOT / "benchmarks" / "cases"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def cmd_validate(path: Path) -> int:
    errors = validate_document(load_json(path))
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID")
    return 0


def cmd_cases() -> int:
    for path in sorted(CASES_DIR.glob("*.json")):
        case = load_json(path)
        print(f"{case['id']}: {case['title']}")
    return 0


def cmd_score(case_path: Path, result_path: Path) -> int:
    result = load_json(result_path)
    errors = validate_document(result)
    if errors:
        print(json.dumps({"valid_schema": False, "errors": errors}, indent=2))
        return 1

    report = score(load_json(case_path), result)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="efrc", description="Validate and benchmark Evidence-First Root Cause outputs.")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate an output against the canonical JSON schema.")
    validate.add_argument("result", type=Path)

    sub.add_parser("cases", help="List included behavioral benchmark cases.")

    score_parser = sub.add_parser("score", help="Score an output against one benchmark case.")
    score_parser.add_argument("case", type=Path)
    score_parser.add_argument("result", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate":
        return cmd_validate(args.result)
    if args.command == "cases":
        return cmd_cases()
    if args.command == "score":
        return cmd_score(args.case, args.result)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
