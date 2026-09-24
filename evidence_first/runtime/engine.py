from __future__ import annotations

import base64
import copy
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from evidence_first.adapters.base import AgentAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.catalog import default_agent_registry
from evidence_first.agents.orchestrator import InvestigationOrchestrator
from evidence_first.agents.result import AgentDecision, AgentResult
from evidence_first.agents.validation import validate_agent_result
from evidence_first.core.causal import DesignStrength
from evidence_first.core.confidence import assess_confidence
from evidence_first.core.investigator import summarize
from evidence_first.core.models import EvidenceKind, EvidenceRecord, Hypothesis
from evidence_first.core.state import InvestigationState
from evidence_first.governance.gates import ConclusionCandidate, evaluate_conclusion
from evidence_first.runtime.audit import build_hash_chain
from evidence_first.runtime.events import InvestigationEvent
from evidence_first.runtime.tool_broker import ToolExecutionBroker, ToolRequest


class Stage(str, Enum):
    INTAKE = "intake"
    PLANNING = "planning"
    SIGNAL_VALIDATION = "signal_validation"
    DATA_QUALITY = "data_quality"
    HYPOTHESES = "hypotheses"
    CONTRADICTION = "contradiction"
    CONFOUND = "confound"
    CONTRIBUTION = "contribution"
    CRITIC = "critic"
    INTERVENTION = "intervention"
    OUTCOME = "outcome"
    MEMORY = "memory"
    AWAITING_OUTCOME = "awaiting_outcome"
    COMPLETE = "complete"
    BLOCKED = "blocked"


ROLE_STAGE = {
    AgentRole.EVIDENCE_INTAKE_COORDINATOR: Stage.INTAKE,
    AgentRole.INVESTIGATION_PLANNER: Stage.PLANNING,
    AgentRole.SIGNAL_VALIDATOR: Stage.SIGNAL_VALIDATION,
    AgentRole.DATA_QUALITY_INVESTIGATOR: Stage.DATA_QUALITY,
    AgentRole.HYPOTHESIS_GENERATOR: Stage.HYPOTHESES,
    AgentRole.EVIDENCE_ANALYST: Stage.HYPOTHESES,
    AgentRole.CONTRADICTION_INVESTIGATOR: Stage.CONTRADICTION,
    AgentRole.CONFOUND_REVIEWER: Stage.CONFOUND,
    AgentRole.CONTRIBUTION_ANALYST: Stage.CONTRIBUTION,
    AgentRole.CRITIC: Stage.CRITIC,
    AgentRole.INTERVENTION_PLANNER: Stage.INTERVENTION,
    AgentRole.OUTCOME_EVALUATOR: Stage.OUTCOME,
    AgentRole.MEMORY_CURATOR: Stage.MEMORY,
}


EXTERNAL_INPUTS = frozenset(
    {
        "source_inventory",
        "post_intervention_evidence",
        "evidence_records",
        "domain",
    }
)


RUNTIME_REQUIRED_INPUTS: dict[AgentRole, tuple[str, ...]] = {
    AgentRole.EVIDENCE_INTAKE_COORDINATOR: ("source_inventory",),
    AgentRole.INVESTIGATION_PLANNER: ("available_evidence_inventory",),
    AgentRole.SIGNAL_VALIDATOR: ("problem_statement", "evidence_ledger"),
    AgentRole.DATA_QUALITY_INVESTIGATOR: ("evidence_ledger",),
    AgentRole.HYPOTHESIS_GENERATOR: ("validated_signal", "evidence_ledger"),
    AgentRole.EVIDENCE_ANALYST: ("hypotheses", "evidence_ledger", "tool_registry"),
    AgentRole.CONTRADICTION_INVESTIGATOR: ("hypotheses", "evidence_ledger"),
    AgentRole.CONFOUND_REVIEWER: ("hypotheses", "evidence_ledger"),
    AgentRole.CONTRIBUTION_ANALYST: (
        "surviving_hypotheses",
        "evidence_ledger",
        "confound_findings",
    ),
    AgentRole.CRITIC: ("draft_conclusion", "evidence_ledger"),
    AgentRole.INTERVENTION_PLANNER: ("critic_approved_conclusion", "evidence_ledger"),
    AgentRole.OUTCOME_EVALUATOR: ("validation_plan", "post_intervention_evidence"),
    AgentRole.MEMORY_CURATOR: ("critic_approved_conclusion", "outcome_assessment"),
}


class AppendOnlyEventLog(list[InvestigationEvent]):
    def __setitem__(self, key, value):
        return None

    def __delitem__(self, key):
        return None

    def clear(self):
        return None

    def pop(self, index=-1):
        return self[-1] if self else None

    def remove(self, value):
        return None

    def reverse(self):
        return None

    def sort(self, *args, **kwargs):
        return None


def _deepcopy_or_raise(value: Any) -> Any:
    return copy.deepcopy(value)


def _quarantine_value(value: Any) -> Any:
    """Remove raw untrusted text from ordinary downstream context.

    The original remains in the stored intake result; downstream model context gets
    content-addressed references rather than verbatim instruction-like strings.
    """
    if isinstance(value, str):
        raw = value.encode("utf-8")
        return {
            "untrusted_ref": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "encoding": "base64",
            "value_b64": base64.b64encode(raw).decode("ascii"),
        }
    if isinstance(value, list):
        return [_quarantine_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_quarantine_value(item) for item in value)
    if isinstance(value, dict):
        return {str(k): _quarantine_value(v) for k, v in value.items()}
    return value


def _ledger_snapshot(state: InvestigationState) -> dict[str, dict[str, Any]]:
    return {
        record.evidence_id: {
            "statement": record.statement,
            "kind": record.kind.value,
            "source": record.source,
            "reliability": record.reliability,
            "content_hash": record.content_hash,
        }
        for record in state.ledger.evidence_records
    }


@dataclass
class InvestigationRun:
    question: str
    inputs: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    state: InvestigationState | None = None
    results: list[AgentResult] = field(default_factory=list)
    events: AppendOnlyEventLog = field(default_factory=AppendOnlyEventLog)
    audit_chain: tuple[str, ...] = ()
    stage: Stage = Stage.PLANNING
    blocked_by: str | None = None
    next_task_index: int = 0

    def artifact_context(self) -> dict[str, Any]:
        merged = _deepcopy_or_raise(self.context)
        merged["inputs"] = _deepcopy_or_raise(self.inputs)
        by_role: dict[str, dict[str, Any]] = {}

        for result in self.results:
            artifacts = _deepcopy_or_raise(result.artifacts)
            if result.role is AgentRole.EVIDENCE_INTAKE_COORDINATOR:
                if "evidence_candidates" in artifacts:
                    artifacts["evidence_candidates"] = _quarantine_value(
                        artifacts["evidence_candidates"]
                    )
            by_role[result.role.value] = artifacts
            for key, value in artifacts.items():
                # First writer wins for shared keys; later agents cannot erase an
                # earlier warning by writing None or a conflicting value.
                if key not in merged:
                    merged[key] = value

        merged["artifacts_by_role"] = by_role
        if self.state is not None:
            merged["evidence_ledger"] = _ledger_snapshot(self.state)
        return merged

    def add_event(self, event: InvestigationEvent) -> None:
        list.append(self.events, event)
        self.audit_chain = build_hash_chain(list(self.events))


class InvestigationEngine:
    def __init__(
        self,
        adapter: AgentAdapter,
        tool_broker: ToolExecutionBroker | None = None,
        max_tool_rounds: int = 3,
        max_tool_requests_per_round: int = 100,
        max_tool_requests_per_run: int = 1_000,
    ):
        self.adapter = adapter
        self.tool_broker = tool_broker
        self.max_tool_rounds = max_tool_rounds
        self.max_tool_requests_per_round = max_tool_requests_per_round
        self.max_tool_requests_per_run = max_tool_requests_per_run
        self.registry = default_agent_registry()
        self.plan = InvestigationOrchestrator().build_plan()

    def _block(
        self,
        run: InvestigationRun,
        actor: str,
        event_type: str,
        message: str,
    ) -> InvestigationRun:
        run.stage = Stage.BLOCKED
        run.blocked_by = actor
        run.add_event(
            InvestigationEvent(
                event_type,
                run.stage.value,
                message,
                actor,
            )
        )
        return run

    def _load_external_evidence(
        self,
        state: InvestigationState,
        records: Any,
    ) -> None:
        if not records:
            return
        for item in records:
            if isinstance(item, EvidenceRecord):
                state.ledger.add_evidence(item)
                continue
            if not isinstance(item, dict):
                raise ValueError("evidence_records items must be EvidenceRecord or dict")
            kind = item.get("kind", EvidenceKind.OBSERVATION)
            if not isinstance(kind, EvidenceKind):
                kind = EvidenceKind(str(kind))
            state.ledger.add_evidence(
                EvidenceRecord(
                    evidence_id=str(item["evidence_id"]),
                    statement=str(item["statement"]),
                    kind=kind,
                    source=str(item["source"]),
                    reliability=float(item.get("reliability", 1.0)),
                    metadata=dict(item.get("metadata", {})),
                )
            )

    def _parse_hypotheses(self, run: InvestigationRun, artifact: Any) -> None:
        if not isinstance(artifact, list):
            return
        for index, item in enumerate(artifact, start=1):
            if not isinstance(item, dict):
                continue
            hid = str(item.get("hypothesis_id") or item.get("id") or f"h{index}")
            if any(h.hypothesis_id == hid for h in run.state.hypotheses.all):
                continue
            run.state.hypotheses.add(
                Hypothesis(
                    hypothesis_id=hid,
                    statement=str(item.get("hypothesis") or item.get("statement") or hid),
                    mechanism=str(item.get("mechanism") or "unspecified"),
                    relationship=str(item.get("relationship") or "competing"),
                )
            )

    def _record_hypothesis_tests(self, run: InvestigationRun, artifact: Any) -> None:
        if not isinstance(artifact, list):
            return
        for item in artifact:
            if not isinstance(item, dict):
                continue
            hid = item.get("hypothesis_id")
            if not hid:
                continue
            for eid in item.get("evidence_for", ()):
                run.state.hypotheses.support(str(hid), str(eid))
            for eid in item.get("evidence_against", ()):
                run.state.hypotheses.contradict(str(hid), str(eid))

    def _critic_gate(
        self,
        run: InvestigationRun,
        result: AgentResult,
    ) -> tuple[bool, str]:
        artifact = result.artifacts.get("critic_approved_conclusion")
        if not artifact:
            return False, "critic did not provide an approved conclusion"

        verdict = str(result.artifacts.get("critic_verdict", "")).strip().lower()
        if verdict in {"reject", "rejected", "revise", "unsupported", "fail"}:
            return False, f"critic verdict is {verdict}"

        summary = summarize(run.state)
        supported = summary.supported_hypotheses
        contributor_count = (
            len(supported)
            if summary.status.value == "multiple_contributors_supported"
            else 1
        )

        known_ids = tuple(r.evidence_id for r in run.state.ledger.evidence_records)
        evidence_ids = result.evidence_ids
        if not evidence_ids and isinstance(artifact, dict):
            raw = artifact.get("evidence_ids", ())
            if isinstance(raw, (list, tuple)):
                evidence_ids = tuple(str(x) for x in raw)

        contradiction_review_complete = any(
            r.role is AgentRole.CONTRADICTION_INVESTIGATOR for r in run.results
        )
        unresolved_confounds = 0
        confounds = run.artifact_context().get("confound_findings")
        if isinstance(confounds, dict):
            raw = confounds.get("unresolved_material_confounds", 0)
            if isinstance(raw, int):
                unresolved_confounds = max(0, raw)

        design = DesignStrength.OBSERVATIONAL
        design_name = run.inputs.get("design_strength")
        if design_name:
            try:
                design = DesignStrength[str(design_name).upper()]
            except (KeyError, TypeError):
                design = DesignStrength.OBSERVATIONAL

        gate = evaluate_conclusion(
            ConclusionCandidate(
                statement=(
                    str(artifact.get("statement", ""))
                    if isinstance(artifact, dict)
                    else str(artifact)
                ),
                evidence_ids=tuple(evidence_ids),
                signal_trustworthy=run.state.signal_validated,
                data_quality_blocked=(
                    run.state.status.value == "data_quality_blocked"
                ),
                competing_hypotheses_tested=len(run.state.hypotheses.all),
                contradiction_review_complete=contradiction_review_complete,
                unresolved_material_confounds=unresolved_confounds,
                known_evidence_ids=known_ids,
                design_strength=design,
                contributor_count=contributor_count,
                supporting_sources=len(set(evidence_ids)),
            )
        )
        run.context["conclusion_gate"] = {
            "allowed": gate.allowed,
            "status": gate.status,
            "reasons": gate.reasons,
        }
        run.context["confidence_assessment"] = assess_confidence(
            supporting_sources=len(set(evidence_ids)),
            contradictions=sum(
                len(h.contradicting_evidence_ids) for h in run.state.hypotheses.all
            ),
            unresolved_confounds=unresolved_confounds,
            design=design,
            signal_valid=run.state.signal_validated,
        )

        if not gate.allowed:
            return False, "; ".join(gate.reasons) or gate.status
        return True, gate.status

    def _run_from_index(
        self,
        run: InvestigationRun,
        start_index: int,
    ) -> InvestigationRun:
        total_tool_requests = len(run.context.get("tool_outcomes", []))

        for index in range(start_index, len(self.plan.tasks)):
            task = self.plan.tasks[index]
            run.next_task_index = index

            if (
                task.role is AgentRole.OUTCOME_EVALUATOR
                and "post_intervention_evidence" not in run.context
            ):
                run.stage = Stage.AWAITING_OUTCOME
                run.next_task_index = index
                run.add_event(
                    InvestigationEvent(
                        "awaiting_outcome",
                        run.stage.value,
                        "Intervention plan complete; post-intervention evidence is required.",
                        "engine",
                    )
                )
                return run

            spec = self.registry[task.role]
            run.stage = ROLE_STAGE[task.role]
            current = run.artifact_context()
            missing_inputs = [
                name
                for name in RUNTIME_REQUIRED_INPUTS.get(task.role, ())
                if name not in current
            ]
            if missing_inputs:
                return self._block(
                    run,
                    task.role.value,
                    "contract_violation",
                    "missing required input(s): " + ", ".join(missing_inputs),
                )

            run.add_event(
                InvestigationEvent(
                    "agent_started",
                    run.stage.value,
                    spec.purpose,
                    task.role.value,
                )
            )

            try:
                result = self.adapter.run(spec, _deepcopy_or_raise(current))
            except KeyboardInterrupt:
                raise
            except BaseException as exc:
                return self._block(
                    run,
                    task.role.value,
                    "agent_error",
                    f"{type(exc).__name__}: {exc}",
                )

            if task.role is AgentRole.EVIDENCE_ANALYST:
                for _ in range(self.max_tool_rounds):
                    if not isinstance(result.artifacts, dict):
                        break
                    requests = result.artifacts.get("tool_requests", [])
                    if not requests:
                        break
                    if not isinstance(requests, list) or any(
                        not isinstance(item, dict)
                        or not isinstance(item.get("name"), str)
                        or not isinstance(item.get("arguments", {}), dict)
                        for item in requests
                    ):
                        return self._block(
                            run,
                            task.role.value,
                            "contract_violation",
                            "malformed tool request",
                        )
                    if len(requests) > self.max_tool_requests_per_round:
                        return self._block(
                            run,
                            task.role.value,
                            "tool_request_budget",
                            "tool request round exceeds configured limit",
                        )
                    if total_tool_requests + len(requests) > self.max_tool_requests_per_run:
                        return self._block(
                            run,
                            task.role.value,
                            "tool_request_budget",
                            "tool request run exceeds configured limit",
                        )
                    if self.tool_broker is None:
                        return self._block(
                            run,
                            task.role.value,
                            "tooling_unavailable",
                            "Evidence Analyst requested tools but no broker is configured.",
                        )

                    parsed = [
                        ToolRequest(
                            str(item["name"]),
                            dict(item.get("arguments", {})),
                            tuple(item.get("source_ids", ())),
                        )
                        for item in requests
                    ]
                    outcomes = self.tool_broker.execute_many(parsed)
                    total_tool_requests += len(requests)
                    run.context.setdefault("tool_outcomes", []).extend(
                        {
                            "name": outcome.name,
                            "ok": outcome.ok,
                            "value": outcome.value,
                            "error": outcome.error,
                            "source_ids": outcome.source_ids,
                        }
                        for outcome in outcomes
                    )
                    run.add_event(
                        InvestigationEvent(
                            "tools_executed",
                            run.stage.value,
                            f"{len(outcomes)} tool outcome(s) recorded.",
                            task.role.value,
                        )
                    )
                    try:
                        result = self.adapter.run(
                            spec,
                            _deepcopy_or_raise(run.artifact_context()),
                        )
                    except KeyboardInterrupt:
                        raise
                    except BaseException as exc:
                        return self._block(
                            run,
                            task.role.value,
                            "agent_error",
                            f"{type(exc).__name__}: {exc}",
                        )

                if (
                    isinstance(result.artifacts, dict)
                    and result.artifacts.get("tool_requests", [])
                ):
                    return self._block(
                        run,
                        task.role.value,
                        "tool_round_limit",
                        f"Evidence Analyst still requested tools after {self.max_tool_rounds} round(s).",
                    )

            violations = validate_agent_result(spec, result)
            if violations:
                return self._block(
                    run,
                    task.role.value,
                    "contract_violation",
                    "; ".join(v.message for v in violations),
                )

            ghost = [
                eid
                for eid in result.evidence_ids
                if eid not in {
                    record.evidence_id for record in run.state.ledger.evidence_records
                }
            ]
            if ghost:
                return self._block(
                    run,
                    task.role.value,
                    "ghost_evidence",
                    "unknown evidence id(s): " + ", ".join(ghost),
                )

            # Store an isolated copy so later agents can never mutate earlier results.
            try:
                stored = AgentResult(
                    role=result.role,
                    decision=result.decision,
                    summary=result.summary,
                    artifacts=_deepcopy_or_raise(result.artifacts),
                    evidence_ids=tuple(result.evidence_ids),
                    unknowns=tuple(result.unknowns),
                    next_requests=tuple(result.next_requests),
                )
            except BaseException as exc:
                return self._block(
                    run,
                    task.role.value,
                    "contract_violation",
                    f"result could not be isolated: {type(exc).__name__}: {exc}",
                )
            run.results.append(stored)

            for unknown in stored.unknowns:
                run.context.setdefault("unknowns", []).append(unknown)

            if task.role is AgentRole.SIGNAL_VALIDATOR:
                sv = stored.artifacts.get("signal_validation_result")
                trustworthy = None
                if isinstance(sv, dict) and "trustworthy" in sv:
                    trustworthy = bool(sv["trustworthy"])
                elif "validated_signal" in stored.artifacts:
                    val = stored.artifacts["validated_signal"]
                    if isinstance(val, dict) and "trustworthy" in val:
                        trustworthy = bool(val["trustworthy"])
                    else:
                        trustworthy = bool(val)
                if trustworthy is False:
                    run.state.mark_signal_validated(False)
                    return self._block(
                        run,
                        task.role.value,
                        "signal_untrustworthy",
                        "signal validator declared the signal untrustworthy",
                    )
                run.state.mark_signal_validated(bool(trustworthy))

            if task.role is AgentRole.HYPOTHESIS_GENERATOR:
                self._parse_hypotheses(run, stored.artifacts.get("hypotheses"))

            if task.role is AgentRole.EVIDENCE_ANALYST:
                derived = stored.artifacts.get("derived_evidence")
                if isinstance(derived, list):
                    try:
                        self._load_external_evidence(run.state, derived)
                    except (ValueError, KeyError, TypeError):
                        return self._block(
                            run,
                            task.role.value,
                            "invalid_derived_evidence",
                            "derived evidence could not be verified",
                        )
                self._record_hypothesis_tests(
                    run,
                    stored.artifacts.get("hypothesis_tests"),
                )

            if task.role is AgentRole.CONTRADICTION_INVESTIGATOR:
                surviving = stored.artifacts.get("surviving_hypotheses")
                if isinstance(surviving, list) and len(surviving) == 0:
                    run.state.mark_insufficient_evidence(
                        "contradiction review eliminated all hypotheses"
                    )
                    return self._block(
                        run,
                        task.role.value,
                        "all_hypotheses_falsified",
                        "no hypothesis survived contradiction review",
                    )

            if task.role is AgentRole.CRITIC:
                allowed, reason = self._critic_gate(run, stored)
                if not allowed:
                    return self._block(
                        run,
                        task.role.value,
                        "critic_rejected",
                        reason,
                    )

            run.add_event(
                InvestigationEvent(
                    "agent_finished",
                    run.stage.value,
                    stored.summary,
                    task.role.value,
                    {"decision": stored.decision.value},
                )
            )

            if stored.decision is AgentDecision.BLOCK:
                return self._block(
                    run,
                    task.role.value,
                    "investigation_blocked",
                    stored.summary,
                )
            if stored.decision is AgentDecision.REVISE:
                return self._block(
                    run,
                    task.role.value,
                    "revision_required",
                    stored.summary,
                )

            run.next_task_index = index + 1

        run.stage = Stage.COMPLETE
        run.add_event(
            InvestigationEvent(
                "investigation_complete",
                run.stage.value,
                "Investigation completed governed sequence.",
                "engine",
            )
        )
        return run

    def run(
        self,
        question: str,
        context: dict[str, Any] | None = None,
    ) -> InvestigationRun:
        supplied = dict(context or {})
        inputs = {
            key: _deepcopy_or_raise(value)
            for key, value in supplied.items()
            if key in EXTERNAL_INPUTS
        }
        inputs.setdefault("source_inventory", ())

        state = InvestigationState(question)
        try:
            self._load_external_evidence(state, inputs.get("evidence_records"))
        except (ValueError, KeyError, TypeError) as exc:
            run = InvestigationRun(
                question=question,
                inputs=inputs,
                context={},
                state=state,
            )
            return self._block(
                run,
                "engine",
                "invalid_external_evidence",
                str(exc),
            )

        context_owned: dict[str, Any] = {
            "problem_statement": question,
            "source_inventory": _deepcopy_or_raise(inputs["source_inventory"]),
            "evidence_ledger": _ledger_snapshot(state),
            "tool_registry": (
                self.tool_broker.registry.names()
                if self.tool_broker is not None
                else ()
            ),
        }
        if "post_intervention_evidence" in inputs:
            context_owned["post_intervention_evidence"] = _deepcopy_or_raise(
                inputs["post_intervention_evidence"]
            )
        if "domain" in inputs:
            context_owned["domain"] = inputs["domain"]

        run = InvestigationRun(
            question=question,
            inputs=inputs,
            context=context_owned,
            state=state,
        )
        return self._run_from_index(run, 0)

    def resume(
        self,
        run: InvestigationRun,
        new_inputs: dict[str, Any],
    ) -> InvestigationRun:
        if run.stage is not Stage.AWAITING_OUTCOME:
            raise ValueError("only an awaiting_outcome run can be resumed")
        allowed = {
            key: _deepcopy_or_raise(value)
            for key, value in new_inputs.items()
            if key in EXTERNAL_INPUTS
        }
        if "post_intervention_evidence" not in allowed:
            raise ValueError("post_intervention_evidence is required to resume")
        run.inputs.update(allowed)
        run.context["post_intervention_evidence"] = _deepcopy_or_raise(
            allowed["post_intervention_evidence"]
        )
        return self._run_from_index(run, run.next_task_index)
