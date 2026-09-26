#!/usr/bin/env python3
"""Evidence-First command-line interface."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

from evidence_first.adapters import JSONModelAdapter
from evidence_first.agents import AgentRole, InvestigationOrchestrator
from evidence_first.agents.artifacts import validate_artifact_flow
from evidence_first.domains import DOMAIN_PACKS
from evidence_first.evaluation.ablation import ablation_plan
from evidence_first.intake import ingest_csv, ingest_json, ingest_text, ingest_xlsx_bytes
from evidence_first.product.config import (
    ProductConfig,
    default_config_path,
    load_config,
    save_config,
)
from evidence_first.product.demo import run_demo
from evidence_first.product.domain import detect_domain, validate_domain
from evidence_first.product.progress import ProgressAdapter
from evidence_first.product.providers import (
    build_json_call,
    parse_command,
    provider_readiness,
)
from evidence_first.product.sources import prepare_sources
from evidence_first.product.workspace import create_run_workspace, write_run_artifacts
from evidence_first.runtime import InvestigationEngine, Stage
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
        "source": {
            "source_id": result.source.source_id,
            "source_type": result.source.source_type,
            "fingerprint": result.source.fingerprint,
            "byte_size": result.source.byte_size,
        },
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


def _prompt(
    label: str,
    *,
    default: str | None = None,
    required: bool = True,
) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""
        print("A value is required.")


def _interactive_config() -> ProductConfig:
    print("Evidence-First provider setup")
    print("1. OpenAI")
    print("2. Anthropic")
    print("3. Command adapter (advanced/local harness)")
    choice = _prompt("Provider", default="1")
    provider = {"1": "openai", "2": "anthropic", "3": "command"}.get(
        choice.lower(),
        choice.lower(),
    )
    model = _prompt("Model name")

    command: tuple[str, ...] = ()
    if provider == "command":
        command = parse_command(
            _prompt(
                "Command (prompt on stdin; JSON on stdout; use {model} if needed)"
            )
        )

    return ProductConfig(
        provider=provider,
        model=model,
        command=command,
    )


def _config_from_args(args, *, persist_if_new: bool = False) -> ProductConfig:
    config_path = getattr(args, "config", None)
    existing = load_config(config_path)

    if existing is None:
        if getattr(args, "provider", None) and getattr(args, "model", None):
            command = ()
            if getattr(args, "provider_command", None):
                command = parse_command(args.provider_command)
            existing = ProductConfig(
                provider=args.provider,
                model=args.model,
                command=command,
                runs_dir=getattr(args, "runs_dir", None) or "runs",
            )
        elif sys.stdin.isatty():
            print(
                f"No Evidence-First config found at "
                f"{config_path or default_config_path()}."
            )
            existing = _interactive_config()
            if persist_if_new:
                path = save_config(existing, config_path)
                print(f"Saved configuration: {path}")
        else:
            raise RuntimeError(
                "No Evidence-First configuration found. Run 'efrc init' or "
                "supply --provider and --model."
            )

    changes = {}
    if getattr(args, "provider", None):
        changes["provider"] = args.provider
    if getattr(args, "model", None):
        changes["model"] = args.model
    if getattr(args, "runs_dir", None):
        changes["runs_dir"] = args.runs_dir
    if getattr(args, "provider_command", None):
        changes["command"] = parse_command(args.provider_command)

    if changes:
        existing = replace(existing, **changes)
    return existing


def cmd_init(args) -> int:
    config = _config_from_args(args, persist_if_new=False)
    path = save_config(config, args.config)
    readiness = provider_readiness(config)

    print(f"Configuration saved: {path}")
    print(f"Provider: {config.provider}")
    print(f"Model: {config.model}")
    print("API keys/tokens are NOT stored in this file.")

    if config.provider == "openai":
        print("Set OPENAI_API_KEY in your environment before investigate.")
    elif config.provider == "anthropic":
        print("Set ANTHROPIC_API_KEY in your environment before investigate.")

    print(json.dumps({"provider_readiness": readiness}, indent=2))
    return 0


def _core_doctor_checks() -> tuple[dict, list]:
    gaps = validate_artifact_flow(InvestigationOrchestrator().build_plan())
    checks = {
        "agents": len(AgentRole),
        "artifact_flow_closed": not gaps,
        "benchmark_cases": len(list(CASES_DIR.glob("*.json"))),
        "domain_packs": len(DOMAIN_PACKS),
        "canonical_schema_exists": (
            ROOT / "schemas" / "root_cause_output.schema.json"
        ).exists(),
        "benchmark_manifest_exists": (
            ROOT / "benchmarks" / "manifest.json"
        ).exists(),
    }
    return checks, gaps


def cmd_doctor(args) -> int:
    checks, gaps = _core_doctor_checks()
    core_ok = (
        checks["agents"] >= 13
        and checks["artifact_flow_closed"]
        and checks["benchmark_cases"] >= 20
        and checks["domain_packs"] >= 6
        and checks["canonical_schema_exists"]
        and checks["benchmark_manifest_exists"]
    )

    config = load_config(args.config)
    readiness = provider_readiness(config) if config else {
        "ready": False,
        "reason": "no provider configuration; run efrc init",
    }

    payload = {
        "status": (
            "PASS"
            if core_ok and (readiness.get("ready") or not args.require_provider)
            else "FAIL"
        ),
        "core": checks,
        "artifact_gaps": [gap.__dict__ for gap in gaps],
        "provider": readiness,
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if payload["status"] == "PASS" else 1


def cmd_demo(args) -> int:
    out = args.out.expanduser().resolve()
    print("Running bundled Evidence-First investigation demo...")
    artifacts = run_demo(out_dir=out, stream=sys.stdout)
    print("")
    print("DEMO COMPLETE")
    print(f"Report: {artifacts['report']}")
    print(f"Workspace: {artifacts['workspace']}")
    return 0


def _interactive_sources() -> list[Path]:
    print(
        "Enter evidence file paths one at a time. Supported: CSV, JSON, TXT/MD, "
        "XLSX/XLSM. Press Enter on an empty line when finished."
    )
    sources: list[Path] = []
    while True:
        value = input("Evidence file: ").strip()
        if not value:
            break
        sources.append(Path(value))
    if not sources:
        raise ValueError("at least one evidence source is required")
    return sources


def cmd_investigate(args) -> int:
    config = _config_from_args(args, persist_if_new=True)
    readiness = provider_readiness(config)
    if not readiness.get("ready"):
        raise RuntimeError(
            "Configured provider is not ready: "
            + json.dumps(readiness, default=str)
        )

    question = args.question
    if not question:
        if not sys.stdin.isatty():
            raise RuntimeError("--question is required in non-interactive mode")
        question = _prompt("What are you investigating?")

    sources = list(args.source or [])
    if not sources:
        if not sys.stdin.isatty():
            raise RuntimeError(
                "At least one --source is required in non-interactive mode"
            )
        sources = _interactive_sources()

    domain = args.domain
    if not domain or domain == "auto":
        domain = detect_domain(question)
    domain = validate_domain(domain)

    print(f"Domain: {domain}")
    print(f"Provider: {config.provider} / {config.model}")
    print(f"Preparing {len(sources)} evidence source(s)...")

    prepared = prepare_sources(sources)
    call = build_json_call(config)
    adapter = ProgressAdapter(
        JSONModelAdapter(call),
        stream=sys.stdout,
    )
    engine = InvestigationEngine(
        adapter,
        tool_broker=prepared.tool_broker,
    )

    context = {
        "source_inventory": prepared.source_inventory,
        "evidence_records": prepared.evidence_records,
        "domain": domain,
    }
    if args.post_outcome:
        context["post_intervention_evidence"] = load_json(args.post_outcome)

    run = engine.run(question, context)

    root = (
        args.out.expanduser().resolve()
        if args.out
        else Path(config.runs_dir).expanduser().resolve()
    )
    workspace = create_run_workspace(root, question)
    artifacts = write_run_artifacts(
        run,
        workspace,
        provider=config.provider,
        model=config.model,
        domain=domain,
        source_inventory=prepared.source_inventory,
    )

    print("")
    print(f"Investigation stage: {run.stage.value}")
    if run.blocked_by:
        print(f"Blocked by: {run.blocked_by}")
    if run.stage is Stage.AWAITING_OUTCOME:
        print(
            "The analysis and intervention plan are complete. Add post-intervention "
            "evidence to evaluate whether the prediction held."
        )
    print(f"Report: {artifacts['report']}")
    print(f"Workspace: {artifacts['workspace']}")

    if run.stage is Stage.BLOCKED:
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="efrc",
        description="Evidence-First investigation and evaluation toolkit.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    cmd = sub.add_parser("init", help="Configure a model provider.")
    cmd.add_argument("--provider", choices=("openai", "anthropic", "command"))
    cmd.add_argument("--model")
    cmd.add_argument("--command", dest="provider_command")
    cmd.add_argument("--runs-dir")
    cmd.add_argument("--config", type=Path)

    cmd = sub.add_parser("doctor", help="Check installation and provider readiness.")
    cmd.add_argument("--config", type=Path)
    cmd.add_argument("--require-provider", action="store_true")

    cmd = sub.add_parser("demo", help="Run the bundled deterministic investigation.")
    cmd.add_argument("--out", type=Path, default=Path(".efrc-demo"))

    cmd = sub.add_parser(
        "investigate",
        help="Investigate a question using your own evidence sources.",
    )
    cmd.add_argument("--question")
    cmd.add_argument(
        "--source",
        action="append",
        type=Path,
        help="Evidence file. Repeat for multiple files.",
    )
    cmd.add_argument(
        "--domain",
        default="auto",
        choices=("auto", *tuple(sorted(DOMAIN_PACKS))),
    )
    cmd.add_argument("--provider", choices=("openai", "anthropic", "command"))
    cmd.add_argument("--model")
    cmd.add_argument("--command")
    cmd.add_argument("--runs-dir")
    cmd.add_argument("--config", type=Path)
    cmd.add_argument("--out", type=Path)
    cmd.add_argument(
        "--post-outcome",
        type=Path,
        help="Optional JSON with post-intervention evidence.",
    )

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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "init":
            return cmd_init(args)
        if args.command == "doctor":
            return cmd_doctor(args)
        if args.command == "demo":
            return cmd_demo(args)
        if args.command == "investigate":
            return cmd_investigate(args)
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
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
