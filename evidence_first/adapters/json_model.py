from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from evidence_first.agents.base import AgentSpec
from evidence_first.agents.result import AgentDecision, AgentResult
from evidence_first.agents.validation import validate_agent_result
from .prompt_builder import build_agent_prompt


JSONCall = Callable[[str], dict[str, Any]]
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "agent_result.schema.json"


class JSONModelAdapter:
    """Provider-neutral fail-closed structured adapter for model APIs."""

    def __init__(self, call: JSONCall):
        self.call = call
        self._schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self._validator = Draft202012Validator(self._schema)

    def run(self, spec: AgentSpec, context: dict[str, object]) -> AgentResult:
        context_summary = json.dumps(context, sort_keys=True, ensure_ascii=True, default=str)
        raw = self.call(build_agent_prompt(spec, context_summary))
        if not isinstance(raw, dict):
            raise ValueError("model output must be a JSON object")

        normalized = copy.deepcopy(raw)
        if isinstance(normalized.get("evidence_ids"), str):
            normalized["evidence_ids"] = [normalized["evidence_ids"]]

        errors = sorted(
            self._validator.iter_errors(normalized),
            key=lambda error: list(error.path),
        )
        if errors:
            detail = "; ".join(
                f"{'.'.join(map(str, e.path)) or '<root>'}: {e.message}"
                for e in errors
            )
            raise ValueError(f"agent_result.schema.json validation failed: {detail}")

        result = AgentResult(
            role=spec.role,
            decision=AgentDecision(normalized["decision"]),
            summary=normalized["summary"],
            artifacts=normalized["artifacts"],
            evidence_ids=tuple(normalized.get("evidence_ids", ())),
            unknowns=tuple(normalized.get("unknowns", ())),
            next_requests=tuple(normalized.get("next_requests", ())),
        )
        violations = validate_agent_result(
            spec,
            result,
            require_outputs=result.decision is AgentDecision.CONTINUE,
        )
        if violations:
            raise ValueError("; ".join(v.message for v in violations))
        return result
