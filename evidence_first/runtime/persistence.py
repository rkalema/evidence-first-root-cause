from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .engine import InvestigationRun


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {
            json.dumps(_json_safe(k), sort_keys=True)
            if not isinstance(k, str)
            else k: _json_safe(v)
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return {"__type__": type(value).__name__, "repr": repr(value)}


def save_run(run: InvestigationRun, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "question": run.question,
        "stage": run.stage.value,
        "blocked_by": run.blocked_by,
        "context": _json_safe(run.context),
        "inputs": _json_safe(run.inputs),
        "results": [
            {
                "role": result.role.value,
                "decision": result.decision.value,
                "summary": result.summary,
                "artifacts": _json_safe(result.artifacts),
                "evidence_ids": list(result.evidence_ids),
                "unknowns": list(result.unknowns),
                "next_requests": list(result.next_requests),
            }
            for result in run.results
        ],
        "events": [_json_safe(event) for event in run.events],
        "audit_chain": list(run.audit_chain),
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False)

    backup = destination.with_suffix(destination.suffix + ".bak")
    if destination.exists():
        shutil.copy2(destination, backup)

    fd, temp_name = tempfile.mkstemp(
        prefix=destination.name + ".",
        suffix=".tmp",
        dir=str(destination.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, destination)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)

    # Always maintain a last-known-good copy, including on the first save.
    shutil.copy2(destination, backup)
