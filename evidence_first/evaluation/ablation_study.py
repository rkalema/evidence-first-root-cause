from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")

SECTIONS = {
    "signal_validator": "### 2. Validate the signal",
    "contradiction_investigator": "### 7. Seek contradictory evidence",
    "confound_reviewer": "### 6. Test hypotheses",
    "critic": "### 10. Assign confidence",
}


def _strip_section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return text
    next_heading = text.find("\n### ", start + len(heading))
    if next_heading < 0:
        return text[:start]
    return text[:start] + text[next_heading + 1:]


def ablation_system_prompt(name: str) -> str:
    if name == "full_system":
        return SKILL
    if name == "skill_only":
        return SKILL
    if name == "no_signal_validation":
        return _strip_section(SKILL, SECTIONS["signal_validator"])
    if name == "no_contradiction":
        return _strip_section(SKILL, SECTIONS["contradiction_investigator"])
    if name == "no_confound_review":
        # Remove the explicit confounding instruction while keeping general testing.
        return SKILL.replace(
            "Can a third variable explain both?\n",
            ""
        ).replace(
            "- common-cause confounding\n",
            ""
        )
    if name == "no_critic":
        text = _strip_section(SKILL, SECTIONS["critic"])
        return text.replace(
            "The objective is to produce the **best-supported explanation that survives attempts to disprove it**.",
            "The objective is to produce the best-supported explanation from the supplied evidence.",
        )
    raise ValueError(f"unknown ablation: {name}")


def ablation_packet(case: dict[str, Any], name: str) -> dict[str, Any]:
    facts = "\n".join(f"- {item}" for item in case["facts"])
    return {
        "case_id": case["id"],
        "mode": name,
        "system": ablation_system_prompt(name),
        "user": (
            "Analyze the incident below and determine the strongest explanation "
            "supported by the evidence. Use only the supplied evidence and do not "
            "invent missing facts.\n\n"
            f"EVIDENCE\n{facts}\n\n"
            f"Set case_id to {case['id']!r}. Return the canonical Evidence-First JSON output contract."
        ),
    }


def validate_ablation_separation() -> None:
    full = ablation_system_prompt("full_system")
    assert "Validate the signal" in full
    assert "Seek contradictory evidence" in full
    assert "Assign confidence" in full

    assert "### 2. Validate the signal" not in ablation_system_prompt("no_signal_validation")
    assert "### 7. Seek contradictory evidence" not in ablation_system_prompt("no_contradiction")
    assert "Can a third variable explain both?" not in ablation_system_prompt("no_confound_review")
    assert "### 10. Assign confidence" not in ablation_system_prompt("no_critic")
