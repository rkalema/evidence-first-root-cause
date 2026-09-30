#!/usr/bin/env python3
"""Prepare, execute, score, and report matched live-model empirical studies."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from evidence_first.evaluation.study import (
    load_manifest,
    prepare_study,
    score_completed_study,
    summarize_study,
    verify_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def _repo_sha() -> str:
    configured = os.environ.get("GITHUB_SHA") or os.environ.get("EFRC_REPOSITORY_SHA")
    if configured:
        return configured
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        start = stripped.find("{")
        if start < 0:
            raise ValueError("model returned no JSON object")
        try:
            parsed, end = decoder.raw_decode(stripped[start:])
        except json.JSONDecodeError as exc:
            raise ValueError(f"model returned invalid JSON: {exc}") from exc
        if stripped[start + end :].strip():
            raise ValueError("model returned trailing text after JSON object")
    if not isinstance(parsed, dict):
        raise ValueError("model response must be a JSON object")
    return parsed


def _openai_call(model: str, system: str, user: str) -> tuple[dict, dict]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("install the OpenAI extra: pip install -e '.[openai]'") from exc

    client = OpenAI()
    t0 = time.perf_counter()
    response = client.responses.create(
        model=model,
        instructions=system,
        input=user,
    )
    elapsed = time.perf_counter() - t0
    text = getattr(response, "output_text", None)
    if not text:
        pieces: list[str] = []
        for item in getattr(response, "output", ()) or ():
            for block in getattr(item, "content", ()) or ():
                value = getattr(block, "text", None)
                if value:
                    pieces.append(value)
        text = "\n".join(pieces)
    usage = getattr(response, "usage", None)
    metadata = {
        "elapsed_seconds": elapsed,
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "provider_request_id": getattr(response, "id", None),
        "provider": "openai",
        "model": model,
    }
    return _parse_json_object(text or ""), metadata


def _anthropic_call(model: str, system: str, user: str, max_tokens: int) -> tuple[dict, dict]:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError("install the Anthropic extra: pip install -e '.[anthropic]'") from exc

    client = Anthropic()
    t0 = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": user}],
    )
    elapsed = time.perf_counter() - t0
    text = "\n".join(
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text" and getattr(block, "text", None)
    )
    usage = getattr(response, "usage", None)
    metadata = {
        "elapsed_seconds": elapsed,
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "provider_request_id": getattr(response, "_request_id", None) or getattr(response, "id", None),
        "provider": "anthropic",
        "model_requested": model,
        "model_returned": getattr(response, "model", None),
    }
    return _parse_json_object(text), metadata


def _command_call(command: str, model: str, packet: dict[str, Any], timeout: int) -> tuple[dict, dict]:
    argv = [token.replace("{model}", model) for token in shlex.split(command)]
    if not argv:
        raise ValueError("command cannot be empty")
    env = dict(os.environ)
    env["EFRC_MODEL"] = model
    t0 = time.perf_counter()
    completed = subprocess.run(
        argv,
        input=json.dumps(packet),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        shell=False,
        env=env,
    )
    elapsed = time.perf_counter() - t0
    if completed.returncode != 0:
        raise RuntimeError(
            f"command provider failed with exit {completed.returncode}: "
            f"{completed.stderr.strip()[:1000]}"
        )
    return _parse_json_object(completed.stdout), {
        "elapsed_seconds": elapsed,
        "input_tokens": None,
        "output_tokens": None,
        "provider_request_id": None,
        "provider": "command",
        "model": model,
    }


def _run_trial(
    provider: str,
    model: str,
    packet: dict[str, Any],
    *,
    command: str | None,
    timeout: int,
    max_tokens: int,
) -> tuple[dict, dict]:
    if provider == "openai":
        return _openai_call(model, packet["system"], packet["user"])
    if provider == "anthropic":
        return _anthropic_call(model, packet["system"], packet["user"], max_tokens)
    if provider == "command":
        if not command:
            raise ValueError("--command is required for provider=command")
        return _command_call(command, model, packet, timeout)
    raise ValueError(f"unsupported provider: {provider}")


def run_study(
    study_dir: Path,
    *,
    command: str | None = None,
    timeout: int = 180,
    max_tokens: int = 4096,
    limit: int | None = None,
) -> dict[str, int]:
    manifest = load_manifest(study_dir / "study-manifest.json")
    verify_manifest(study_dir, manifest)
    outputs = study_dir / "outputs"
    metadata_dir = study_dir / "metadata"
    outputs.mkdir(exist_ok=True)
    metadata_dir.mkdir(exist_ok=True)

    completed = skipped = failed = attempted = 0
    errors: list[dict[str, str]] = []
    for trial in sorted(manifest["trials"], key=lambda item: item["order_index"]):
        if limit is not None and attempted >= limit:
            break
        safe_id = trial["trial_id"].replace(":", "__")
        output_path = outputs / f"{safe_id}.json"
        metadata_path = metadata_dir / f"{safe_id}.json"
        if output_path.exists() and metadata_path.exists():
            skipped += 1
            continue

        packet = json.loads((study_dir / trial["prompt_path"]).read_text(encoding="utf-8"))
        attempted += 1
        try:
            result, meta = _run_trial(
                manifest["provider"],
                manifest["model"],
                packet,
                command=command,
                timeout=timeout,
                max_tokens=max_tokens,
            )
            if result.get("case_id") is None:
                result["case_id"] = trial["case_id"]
            output_path.write_text(
                json.dumps(result, indent=2, sort_keys=True, allow_nan=False),
                encoding="utf-8",
            )
            meta.update(
                {
                    "trial_id": trial["trial_id"],
                    "case_id": trial["case_id"],
                    "condition": trial["condition"],
                    "repetition": trial["repetition"],
                    "order_index": trial["order_index"],
                    "prompt_sha256": trial["prompt_sha256"],
                }
            )
            metadata_path.write_text(
                json.dumps(meta, indent=2, sort_keys=True, allow_nan=False),
                encoding="utf-8",
            )
            completed += 1
        except Exception as exc:
            failed += 1
            error_text = f"{type(exc).__name__}: {exc}"
            errors.append({"trial_id": trial["trial_id"], "error": error_text})
            metadata_path.write_text(
                json.dumps(
                    {
                        "trial_id": trial["trial_id"],
                        "case_id": trial["case_id"],
                        "condition": trial["condition"],
                        "error": error_text,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

    return {
        "attempted": attempted,
        "completed": completed,
        "skipped": skipped,
        "failed": failed,
        "errors": errors[:5],
    }


def score_study(study_dir: Path) -> dict[str, Any]:
    rows, missing = score_completed_study(study_dir)
    scores_path = study_dir / "scored-results.json"
    scores_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    manifest = load_manifest(study_dir / "study-manifest.json")
    summary = summarize_study(rows, seed=int(manifest["seed"]))
    payload = {"summary": summary, "missing_trials": missing}
    (study_dir / "study-summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return payload


def report_study(study_dir: Path) -> Path:
    payload = json.loads((study_dir / "study-summary.json").read_text(encoding="utf-8"))
    summary = payload["summary"]
    lines = [
        "# Evidence-First Empirical Study",
        "",
        "Observed results from the prepared matched-condition study.",
        "Synthetic benchmark results do not establish general performance on real-world investigations.",
        "",
        "## Condition results",
        "",
        "| Condition | n | Mean score | Median | Pass rate | Schema valid | Mean latency (s) | Input tokens | Output tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for condition, row in summary["conditions"].items():
        lines.append(
            f"| {condition} | {row['n']} | {row['mean_score']:.3f} | "
            f"{row['median_score']:.3f} | {row['pass_rate']:.1%} | "
            f"{row['schema_valid_rate']:.1%} | {row['mean_elapsed_seconds'] or 'n/a'} | "
            f"{row['total_input_tokens']} | {row['total_output_tokens']} |"
        )
    paired = summary["paired"]
    lines += [
        "",
        "## Paired comparison",
        "",
        f"- Pairs: {paired['n_pairs']}",
        f"- Mean score delta (Evidence-First − baseline): {paired['mean_score_delta']}",
        f"- Median score delta: {paired['median_score_delta']}",
        f"- Wins / ties / losses: {paired['wins']} / {paired['ties']} / {paired['losses']}",
        f"- Two-sided exact sign-test p-value: {paired['two_sided_sign_test_p']}",
        f"- Bootstrap 95% CI for mean delta: {paired['bootstrap_95pct_ci_mean_delta']}",
        "",
        "## False causal conclusion rate",
        "",
    ]
    for condition, rate in summary["false_causal_rate"].items():
        lines.append(f"- {condition}: {rate:.1%}")
    if payload["missing_trials"]:
        lines += ["", "## Missing trials", ""]
        lines += [f"- {item}" for item in payload["missing_trials"]]
    path = study_dir / "STUDY_REPORT.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--provider", choices=("openai", "anthropic", "command"), required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--repetitions", type=int, default=3)
    p.add_argument("--seed", type=int, default=20260928)
    p.add_argument("--repository-sha", default=None)

    p = sub.add_parser("run")
    p.add_argument("study_dir", type=Path)
    p.add_argument("--command")
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--limit", type=int)

    p = sub.add_parser("score")
    p.add_argument("study_dir", type=Path)

    p = sub.add_parser("report")
    p.add_argument("study_dir", type=Path)

    args = parser.parse_args()
    if args.cmd == "prepare":
        path = prepare_study(
            args.out,
            provider=args.provider,
            model=args.model,
            repository_sha=args.repository_sha or _repo_sha(),
            repetitions=args.repetitions,
            seed=args.seed,
        )
        print(path)
        return 0
    if args.cmd == "run":
        print(json.dumps(run_study(
            args.study_dir,
            command=args.command,
            timeout=args.timeout,
            max_tokens=args.max_tokens,
            limit=args.limit,
        ), indent=2))
        return 0
    if args.cmd == "score":
        print(json.dumps(score_study(args.study_dir), indent=2))
        return 0
    print(report_study(args.study_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
