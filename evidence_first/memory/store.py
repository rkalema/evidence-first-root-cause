from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

_MEMORY_KEY = os.environ.get("EFRC_MEMORY_HMAC_KEY", "").encode("utf-8") or os.urandom(32)


@dataclass(frozen=True)
class MemoryEntry:
    investigation_id: str
    hypothesis: str
    outcome: str
    decisive_evidence_ids: tuple[str, ...]
    intervention_result: str | None = None


def _signature(text: str) -> str:
    return hmac.new(_MEMORY_KEY, text.encode("utf-8"), hashlib.sha256).hexdigest()


class InvestigationMemory:
    """Explicit, inspectable memory. Previous conclusions are context, never evidence."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._entries: list[MemoryEntry] = []
        if self.path and self.path.exists():
            self._load_resilient()

    @property
    def _backup(self) -> Path | None:
        return self.path.with_suffix(self.path.suffix + ".bak") if self.path else None

    @property
    def _sigfile(self) -> Path | None:
        return self.path.with_suffix(self.path.suffix + ".sig") if self.path else None

    def _decode(self, text: str) -> list[MemoryEntry]:
        raw = json.loads(text)
        if not isinstance(raw, list):
            raise ValueError("memory root must be a list")
        entries: list[MemoryEntry] = []
        for row in raw:
            if not isinstance(row, dict):
                raise ValueError("memory entry must be an object")
            allowed = {
                "investigation_id",
                "hypothesis",
                "outcome",
                "decisive_evidence_ids",
                "intervention_result",
            }
            if set(row) - allowed:
                raise ValueError("unknown memory fields")
            row = dict(row)
            row["decisive_evidence_ids"] = tuple(row["decisive_evidence_ids"])
            entries.append(MemoryEntry(**row))
        return entries

    def _verified_text(self, path: Path) -> str:
        text = path.read_text(encoding="utf-8")
        if path == self.path and self._sigfile and self._sigfile.exists():
            expected = self._sigfile.read_text(encoding="utf-8").strip()
            if not hmac.compare_digest(expected, _signature(text)):
                raise ValueError("memory integrity check failed")
        return text

    def _load_resilient(self) -> None:
        try:
            text = self._verified_text(self.path)
            self._entries = self._decode(text)
            return
        except (OSError, ValueError, json.JSONDecodeError, TypeError, KeyError):
            pass

        backup = self._backup
        if backup and backup.exists():
            try:
                self._entries = self._decode(backup.read_text(encoding="utf-8"))
                return
            except (OSError, ValueError, json.JSONDecodeError, TypeError, KeyError):
                pass

        self._entries = []

    def _persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps([asdict(entry) for entry in self._entries], indent=2, sort_keys=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, self.path)
        if self._backup:
            shutil.copy2(self.path, self._backup)
        if self._sigfile:
            self._sigfile.write_text(_signature(text), encoding="utf-8")

    def add(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)
        self._persist()

    def search(self, text: str) -> tuple[MemoryEntry, ...]:
        query = text.lower()
        return tuple(
            entry
            for entry in self._entries
            if query in entry.hypothesis.lower() or query in entry.outcome.lower()
        )

    def all(self) -> tuple[MemoryEntry, ...]:
        return tuple(self._entries)
