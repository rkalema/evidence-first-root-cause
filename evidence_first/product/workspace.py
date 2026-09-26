from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from collections.abc import Mapping

from evidence_first.reporting import render_investigation_report
from evidence_first.runtime import InvestigationRun, save_run


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return (slug or "investigation")[:48]


def create_run_workspace(
    runs_dir: Path,
    question: str,
) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = runs_dir / f"{stamp}-{_slug(question)}"
    candidate = base
    counter = 2
    while candidate.exists():
        candidate = Path(str(base) + f"-{counter}")
        counter += 1
    candidate.mkdir(parents=False)
    return candidate


def write_run_artifacts(
    run: InvestigationRun,
    workspace: Path,
    *,
    provider: str,
    model: str,
    domain: str | None,
    source_inventory: tuple[dict[str, Any], ...],
) -> dict[str, Path]:
    workspace.mkdir(parents=True, exist_ok=True)

    run_path = workspace / "run.json"
    save_run(run, run_path)

    report_path = workspace / "report.md"
    report_path.write_text(
        render_investigation_report(run),
        encoding="utf-8",
    )

    evidence = []
    if run.state is not None:
        evidence = [
            {
                "evidence_id": record.evidence_id,
                "statement": record.statement,
                "kind": record.kind.value,
                "source": record.source,
                "reliability": record.reliability,
                "content_hash": record.content_hash,
                "metadata": _json_safe(record.metadata),
            }
            for record in run.state.ledger.evidence_records
        ]
    evidence_path = workspace / "evidence.json"
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    hypotheses = []
    if run.state is not None:
        hypotheses = [
            {
                "hypothesis_id": hypothesis.hypothesis_id,
                "statement": hypothesis.statement,
                "mechanism": hypothesis.mechanism,
                "relationship": hypothesis.relationship,
                "status": hypothesis.status.value,
                "supporting_evidence_ids": hypothesis.supporting_evidence_ids,
                "contradicting_evidence_ids": hypothesis.contradicting_evidence_ids,
            }
            for hypothesis in run.state.hypotheses.all
        ]
    hypotheses_path = workspace / "hypotheses.json"
    hypotheses_path.write_text(
        json.dumps(hypotheses, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    audit_path = workspace / "audit.json"
    audit_path.write_text(
        json.dumps(
            {
                "events": [_json_safe(event) for event in run.events],
                "audit_chain": list(run.audit_chain),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = {
        "question": run.question,
        "stage": run.stage.value,
        "blocked_by": run.blocked_by,
        "conclusion_gate": _json_safe(run.context.get("conclusion_gate")),
        "confidence_assessment": _json_safe(
            run.context.get("confidence_assessment")
        ),
        "artifacts_by_role": _json_safe(
            run.artifact_context().get("artifacts_by_role", {})
        ),
    }
    result_path = workspace / "result.json"
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": run.question,
        "domain": domain,
        "provider": provider,
        "model": model,
        "stage": run.stage.value,
        "sources": [
            {
                "source_id": item["source_id"],
                "fingerprint": item["fingerprint"],
                "source_type": item["source_type"],
                "byte_size": item["byte_size"],
            }
            for item in source_inventory
        ],
        "files": [
            "run.json",
            "report.md",
            "evidence.json",
            "hypotheses.json",
            "audit.json",
            "result.json",
        ],
    }
    manifest_path = workspace / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return {
        "workspace": workspace,
        "run": run_path,
        "report": report_path,
        "evidence": evidence_path,
        "hypotheses": hypotheses_path,
        "audit": audit_path,
        "result": result_path,
        "manifest": manifest_path,
    }
