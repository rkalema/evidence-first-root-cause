from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.evaluate_runner import prompt_packet, score_result

ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT / "benchmarks" / "cases"


@dataclass(frozen=True)
class TrialSpec:
    trial_id: str
    case_id: str
    condition: str
    repetition: int
    order_index: int
    prompt_path: str
    prompt_sha256: str


@dataclass(frozen=True)
class StudyManifest:
    version: int
    seed: int
    repetitions: int
    provider: str
    model: str
    repository_sha: str
    trials: tuple[TrialSpec, ...]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_ids() -> tuple[str, ...]:
    return tuple(sorted(path.stem for path in CASES_DIR.glob("*.json")))


def prepare_study(
    out_dir: Path,
    *,
    provider: str,
    model: str,
    repository_sha: str,
    repetitions: int = 3,
    seed: int = 20260928,
) -> Path:
    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")
    out_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = out_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)

    trials: list[TrialSpec] = []
    for repetition in range(1, repetitions + 1):
        for cid in case_ids():
            for condition in ("baseline", "evidence-first"):
                packet = prompt_packet(cid, condition)
                serialized = json.dumps(packet, indent=2, sort_keys=True)
                if '"expected"' in serialized or '"pass_score"' in serialized:
                    raise ValueError(f"gold leakage detected in prompt for {cid}/{condition}")
                prompt_name = f"{cid}.r{repetition}.{condition}.json"
                path = prompts_dir / prompt_name
                path.write_text(serialized, encoding="utf-8")
                trials.append(
                    TrialSpec(
                        trial_id=f"{cid}:r{repetition}:{condition}",
                        case_id=cid,
                        condition=condition,
                        repetition=repetition,
                        order_index=-1,
                        prompt_path=str(path.relative_to(out_dir)),
                        prompt_sha256=sha256_file(path),
                    )
                )

    rng = random.Random(seed)
    rng.shuffle(trials)
    ordered = tuple(
        TrialSpec(**{**asdict(trial), "order_index": index})
        for index, trial in enumerate(trials, start=1)
    )
    manifest = StudyManifest(
        version=1,
        seed=seed,
        repetitions=repetitions,
        provider=provider,
        model=model,
        repository_sha=repository_sha,
        trials=ordered,
    )
    manifest_path = out_dir / "study-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                **asdict(manifest),
                "trials": [asdict(trial) for trial in ordered],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return manifest_path


def load_manifest(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("version") != 1:
        raise ValueError("unsupported study manifest version")
    return raw


def verify_manifest(study_dir: Path, manifest: dict[str, Any]) -> None:
    seen: set[str] = set()
    for trial in manifest["trials"]:
        trial_id = trial["trial_id"]
        if trial_id in seen:
            raise ValueError(f"duplicate trial id: {trial_id}")
        seen.add(trial_id)
        prompt = study_dir / trial["prompt_path"]
        if not prompt.exists():
            raise ValueError(f"missing prompt: {prompt}")
        if sha256_file(prompt) != trial["prompt_sha256"]:
            raise ValueError(f"prompt hash mismatch: {trial_id}")
        text = prompt.read_text(encoding="utf-8")
        if '"expected"' in text or '"pass_score"' in text:
            raise ValueError(f"gold leakage in prepared prompt: {trial_id}")


def score_completed_study(study_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    manifest = load_manifest(study_dir / "study-manifest.json")
    verify_manifest(study_dir, manifest)
    rows: list[dict[str, Any]] = []
    missing: list[str] = []

    for trial in manifest["trials"]:
        output = study_dir / "outputs" / f"{trial['trial_id'].replace(':', '__')}.json"
        metadata = study_dir / "metadata" / f"{trial['trial_id'].replace(':', '__')}.json"
        if not output.exists():
            missing.append(trial["trial_id"])
            continue
        scored = score_result(trial["case_id"], output)
        result_doc = json.loads(output.read_text(encoding="utf-8"))
        meta = json.loads(metadata.read_text(encoding="utf-8")) if metadata.exists() else {}
        case = json.loads((CASES_DIR / f"{trial['case_id']}.json").read_text(encoding="utf-8"))
        rows.append(
            {
                "trial_id": trial["trial_id"],
                "case_id": trial["case_id"],
                "condition": trial["condition"],
                "repetition": trial["repetition"],
                "order_index": trial["order_index"],
                "expected_status": case["expected"]["status"],
                "actual_status": result_doc.get("status"),
                "score": float(scored.get("score", 0)),
                "passed": bool(scored.get("passed", False)),
                "valid_schema": bool(scored.get("valid_schema", False)),
                "elapsed_seconds": meta.get("elapsed_seconds"),
                "input_tokens": meta.get("input_tokens"),
                "output_tokens": meta.get("output_tokens"),
                "provider_request_id": meta.get("provider_request_id"),
                "output_sha256": sha256_file(output),
            }
        )
    return rows, missing


def _paired_deltas(rows: list[dict[str, Any]]) -> list[float]:
    pairs: dict[tuple[str, int], dict[str, float]] = {}
    for row in rows:
        key = (row["case_id"], int(row["repetition"]))
        pairs.setdefault(key, {})[row["condition"]] = float(row["score"])
    return [
        pair["evidence-first"] - pair["baseline"]
        for pair in pairs.values()
        if "baseline" in pair and "evidence-first" in pair
    ]


def _sign_test_pvalue(deltas: list[float]) -> float | None:
    nonzero = [delta for delta in deltas if delta != 0]
    n = len(nonzero)
    if n == 0:
        return None
    positive = sum(delta > 0 for delta in nonzero)
    k = min(positive, n - positive)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def _bootstrap_mean_ci(
    values: list[float],
    *,
    seed: int,
    iterations: int = 10000,
) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(iterations):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(iterations * 0.025)]
    hi = means[min(iterations - 1, int(iterations * 0.975))]
    return round(lo, 3), round(hi, 3)


def summarize_study(rows: list[dict[str, Any]], *, seed: int) -> dict[str, Any]:
    by_condition: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_condition.setdefault(row["condition"], []).append(row)

    conditions: dict[str, Any] = {}
    for condition, items in sorted(by_condition.items()):
        n = len(items)
        scores = [float(item["score"]) for item in items]
        conditions[condition] = {
            "n": n,
            "mean_score": round(statistics.fmean(scores), 3) if scores else 0,
            "median_score": round(statistics.median(scores), 3) if scores else 0,
            "pass_rate": round(sum(bool(item["passed"]) for item in items) / n, 4) if n else 0,
            "schema_valid_rate": round(sum(bool(item["valid_schema"]) for item in items) / n, 4) if n else 0,
            "mean_elapsed_seconds": round(
                statistics.fmean(
                    float(item["elapsed_seconds"])
                    for item in items
                    if item.get("elapsed_seconds") is not None
                ),
                3,
            ) if any(item.get("elapsed_seconds") is not None for item in items) else None,
            "total_input_tokens": sum(int(item.get("input_tokens") or 0) for item in items),
            "total_output_tokens": sum(int(item.get("output_tokens") or 0) for item in items),
        }

    deltas = _paired_deltas(rows)
    lo, hi = _bootstrap_mean_ci(deltas, seed=seed)
    causal_expected_noncausal = {"insufficient_evidence", "data_quality_blocked"}
    causal_actual = {"root_cause_supported", "multiple_contributors_supported"}

    false_causal: dict[str, float] = {}
    for condition, items in by_condition.items():
        eligible = [item for item in items if item["expected_status"] in causal_expected_noncausal]
        false_causal[condition] = round(
            sum(item["actual_status"] in causal_actual for item in eligible) / len(eligible),
            4,
        ) if eligible else 0.0

    return {
        "conditions": conditions,
        "paired": {
            "n_pairs": len(deltas),
            "mean_score_delta": round(statistics.fmean(deltas), 3) if deltas else None,
            "median_score_delta": round(statistics.median(deltas), 3) if deltas else None,
            "wins": sum(delta > 0 for delta in deltas),
            "ties": sum(delta == 0 for delta in deltas),
            "losses": sum(delta < 0 for delta in deltas),
            "two_sided_sign_test_p": _sign_test_pvalue(deltas),
            "bootstrap_95pct_ci_mean_delta": [lo, hi],
        },
        "false_causal_rate": false_causal,
    }
