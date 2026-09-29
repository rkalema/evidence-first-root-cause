#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmarks"
MANIFEST = BENCH / "manifest.json"


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("algorithm") != "git-blob-sha1":
        raise SystemExit("unsupported benchmark manifest algorithm")

    failures = []
    for item in manifest.get("files", []):
        path = BENCH / item["path"]
        if not path.exists():
            failures.append(f"missing: {item['path']}")
            continue
        actual = git_blob_sha1(path)
        if actual != item["git_blob_sha1"]:
            failures.append(
                f"hash mismatch: {item['path']} expected {item['git_blob_sha1']} got {actual}"
            )

    expected_paths = {item["path"] for item in manifest.get("files", [])}
    actual_paths = {
        str(path.relative_to(BENCH)).replace("\\", "/")
        for path in (BENCH / "cases").glob("*.json")
    }
    missing_from_manifest = sorted(actual_paths - expected_paths)
    if missing_from_manifest:
        failures.append(
            "unmanifested cases: " + ", ".join(missing_from_manifest)
        )

    if failures:
        print("BENCHMARK MANIFEST INVALID")
        for failure in failures:
            print("-", failure)
        return 1

    print(f"BENCHMARK MANIFEST VALID: {len(expected_paths)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
