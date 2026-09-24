#!/usr/bin/env python3
"""CLI for Evidence-First."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_first.agents import AgentRole, InvestigationOrchestrator
from evidence_first.agents.artifacts import validate_artifact_flow
from evidence_first.domains import DOMAIN_PACKS
from evidence_first.evaluation.ablation import ablation_plan
from evidence_first.intake import ingest_csv, ingest_json, ingest_text, ingest_xlsx_bytes
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
    paths = sorted(CASES_DIR.glob("*.json"))
    for path in paths:
        case = load_json(path)
        print(f"{case['id']}: {case['title']}")
    print(f"TOTAL: {len(paths)}")
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


def cmd_intake(path: Path) -> int:
    ext = path.suffix.lower()
    if ext in {".xlsx", ".xlsm"}:
        result = ingest_xlsx_bytes(path.read_bytes(), source_id=path.name)
    else:
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            print(json.dumps({"valid": False, "error": f"decode error: {exc}"}))
            return 1
        if ext == ".csv":
            result = ingest_csv(text, source_id=path.name, raw_bytes=raw)
        elif ext == ".json":
            result = ingest_json(text, source_id=path.name, raw_bytes=raw)
        else:
            result = ingest_text(text, source_id=path.name, raw_bytes=raw)

    payload = {
        "valid": result.valid,
        "source": result.source.__dict__,
        "stats": result.stats,
        "issues": [
            {
                "code": issue.code,
                "message": issue.message,
                "severity": issue.severity.value,
            }
            for issue in result.issues
        ],
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if result.valid else 1


def cmd_doctor() -> int:
    gaps = validate_artifact_flow(InvestigationOrchestrator().build_plan())
    checks = {
        "agents": len(AgentRole),
        "artifact_flow_closed": not gaps,
        "benchmark_cases": len(list(CASES_DIR.glob("*.json"))),
        "domain_packs": len(DOMAIN_PACKS),
        "canonical_schema_exists": (ROOT / "schemas" / "root_cause_output.schema.json").exists(),
    }
    ok = (
        checks["agents"] >= 13
        and checks["artifact_flow_closed"]
        and checks["benchmark_cases"] >= 20
        and checks["domain_packs"] >= 6
        and checks["canonical_schema_exists"]
    )
    print(
        json.dumps(
            {
                "status": "PASS" if ok else "FAIL",
                "checks": checks,
                "artifact_gaps": [gap.__dict__ for gap in gaps],
            },
            indent=2,
        )
    )
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="efrc",
        description="Evidence-First investigation and evaluation toolkit.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    cmd = sub.add_parser("validate")
    cmd.add_argument("result", type=Path)

    sub.add_parser("cases")

    cmd = sub.add_parser("score")
    cmd.add_argument("case", type=Path)
    cmd.add_argument("result", type=Path)

    cmd = sub.add_parser("intake")
    cmd.add_argument("source", type=Path)

    sub.add_parser("domains")
    sub.add_parser("ablations")
    sub.add_parser("doctor")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate":
        return cmd_validate(args.result)
    if args.command == "cases":
        return cmd_cases()
    if args.command == "score":
        return cmd_score(args.case, args.result)
    if args.command == "intake":
        return cmd_intake(args.source)
    if args.command == "domains":
        print("\n".join(sorted(DOMAIN_PACKS)))
        return 0
    if args.command == "ablations":
        print(json.dumps(ablation_plan(), indent=2))
        return 0
    if args.command == "doctor":
        return cmd_doctor()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
