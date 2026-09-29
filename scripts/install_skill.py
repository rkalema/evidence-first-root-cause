#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SKILL_FILES = (
    "SKILL.md",
    "schemas/root_cause_output.schema.json",
    "docs/METHODOLOGY.md",
    "docs/DOMAIN_PACKS.md",
    "docs/LIMITATIONS.md",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install only agent-visible Evidence-First skill material."
    )
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()

    if args.destination.exists():
        raise SystemExit(f"destination already exists: {args.destination}")

    args.destination.mkdir(parents=True)
    for relative in SKILL_FILES:
        source = args.source / relative
        if not source.exists():
            raise SystemExit(f"required skill file missing: {relative}")
        destination = args.destination / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    # Evaluation assets, benchmarks, gold keys, tests, scorers, and trap catalogs
    # are intentionally excluded from the agent-visible installation tree.
    print(args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
