from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
from dataclasses import asdict, dataclass, fields
from pathlib import Path

_LEDGER_KEY = os.environ.get("EFRC_EXPERIMENT_HMAC_KEY", "").encode("utf-8") or os.urandom(32)


@dataclass(frozen=True)
class RunRecord:
    case_id: str
    condition: str
    model: str
    repository_sha: str
    prompt_path: str
    output_path: str
    score: float
    passed: bool
    elapsed_seconds: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    tool_calls: int | None = None
    output_sha256: str | None = None


def _sign(text: str) -> str:
    return hmac.new(_LEDGER_KEY, text.encode("utf-8"), hashlib.sha256).hexdigest()


class ExperimentLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    @property
    def _backup(self) -> Path:
        return self.path.with_suffix(self.path.suffix + ".bak")

    @property
    def _sigfile(self) -> Path:
        return self.path.with_suffix(self.path.suffix + ".sig")

    def _verify_current(self) -> bool:
        if not self.path.exists() or not self._sigfile.exists():
            return False
        text = self.path.read_text(encoding="utf-8")
        expected = self._sigfile.read_text(encoding="utf-8").strip()
        return hmac.compare_digest(expected, _sign(text))

    def append(self, record: RunRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing = self.path.read_text(encoding="utf-8") if self.path.exists() and self._verify_current() else ""
        line = json.dumps(asdict(record), sort_keys=True, allow_nan=False)
        text = existing + line + "\n"
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, self.path)
        shutil.copy2(self.path, self._backup)
        self._sigfile.write_text(_sign(text), encoding="utf-8")

    def _read_text(self) -> str:
        if self._verify_current():
            return self.path.read_text(encoding="utf-8")
        if self._backup.exists():
            return self._backup.read_text(encoding="utf-8")
        return ""

    def read(self) -> tuple[RunRecord, ...]:
        if not self.path.exists() and not self._backup.exists():
            return ()
        allowed = {field.name for field in fields(RunRecord)}
        rows: list[RunRecord] = []
        for line in self._read_text().splitlines():
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                if not isinstance(raw, dict) or set(raw) - allowed:
                    continue
                rows.append(RunRecord(**raw))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        return tuple(rows)
