#!/usr/bin/env python3
"""Controlled baseline-vs-Evidence-First evaluation runner."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.evaluate_case import score
from scripts.validate_output import validate_document

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "cases"

BASELINE_SYSTEM = "You are an analytical assistant. Use only supplied evidence. Do not invent facts."
EF_SYSTEM = (
    "Use the Evidence-First Root Cause method exactly. Preserve uncertainty, "
    "test alternatives, seek contradictions, and do not invent evidence."
)


def load_case(case_id: str) -> dict:
    return json.loads((CASES / f"{case_id}.json").read_text(encoding="utf-8"))


def user_prompt(case: dict) -> str:
    facts = "\n".join(f"- {x}" for x in case["facts"])
    return (
        f'{case["prompt"]}\n\n'
        f"EVIDENCE\n{facts}\n\n"
        "Return the canonical Evidence-First JSON output contract."
    )


def prompt_packet(case_id: str, mode: str) -> dict:
    case = load_case(case_id)
    if mode not in {"baseline", "evidence-first"}:
        raise ValueError(mode)
    return {
        "case_id": case_id,
        "mode": mode,
        "system": BASELINE_SYSTEM if mode == "baseline" else EF_SYSTEM,
        "user": user_prompt(case),
    }


def prepare(case_id: str, out: Path) -> tuple[Path, Path]:
    out.mkdir(parents=True, exist_ok=True)
    baseline = out / f"{case_id}.baseline.prompt.json"
    evidence_first = out / f"{case_id}.evidence-first.prompt.json"
    baseline.write_text(json.dumps(prompt_packet(case_id, "baseline"), indent=2), encoding="utf-8")
    evidence_first.write_text(json.dumps(prompt_packet(case_id, "evidence-first"), indent=2), encoding="utf-8")
    return baseline, evidence_first


def score_result(case_id: str, result_path: Path) -> dict:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate_document(result)
    if errors:
        return {"valid_schema": False, "errors": errors, "passed": False, "score": 0}
    return {"valid_schema": True, **score(load_case(case_id), result)}


def compare(case_id: str, baseline: Path, evidence_first: Path) -> dict:
    baseline_score = score_result(case_id, baseline)
    evidence_first_score = score_result(case_id, evidence_first)
    return {
        "case_id": case_id,
        "baseline": baseline_score,
        "evidence_first": evidence_first_score,
        "delta": round(
            float(evidence_first_score.get("score", 0))
            - float(baseline_score.get("score", 0)),
            1,
        ),
    }


def suite(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = [
        compare(
            item["case_id"],
            Path(item["baseline"]),
            Path(item["evidence_first"]),
        )
        for item in manifest
    ]
    baseline_scores = [float(x["baseline"].get("score", 0)) for x in rows]
    evidence_first_scores = [float(x["evidence_first"].get("score", 0)) for x in rows]
    n = len(rows)
    return {
        "n": n,
        "baseline_mean": round(sum(baseline_scores) / n, 2) if n else 0,
        "evidence_first_mean": round(sum(evidence_first_scores) / n, 2) if n else 0,
        "mean_delta": round((sum(evidence_first_scores) - sum(baseline_scores)) / n, 2) if n else 0,
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    cmd = sub.add_parser("prepare")
    cmd.add_argument("case_id")
    cmd.add_argument("--out", type=Path, default=Path("runs"))

    cmd = sub.add_parser("score")
    cmd.add_argument("case_id")
    cmd.add_argument("result", type=Path)

    cmd = sub.add_parser("compare")
    cmd.add_argument("case_id")
    cmd.add_argument("baseline", type=Path)
    cmd.add_argument("evidence_first", type=Path)

    cmd = sub.add_parser("suite")
    cmd.add_argument("manifest", type=Path)

    args = parser.parse_args()

    if args.cmd == "prepare":
        print("\n".join(map(str, prepare(args.case_id, args.out))))
        return 0
    if args.cmd == "score":
        report = score_result(args.case_id, args.result)
        print(json.dumps(report, indent=2))
        return 0 if report.get("passed") else 1
    if args.cmd == "compare":
        print(json.dumps(compare(args.case_id, args.baseline, args.evidence_first), indent=2))
        return 0

    print(json.dumps(suite(args.manifest), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
