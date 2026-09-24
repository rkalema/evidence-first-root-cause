"""RT-11 Partial-system failure and recovery."""
from __future__ import annotations

import json

from evidence_first.adapters.scripted import ScriptedAdapter
from evidence_first.agents.base import AgentRole
from evidence_first.agents.result import AgentDecision, AgentResult
from evidence_first.evaluation.record import ExperimentLedger, RunRecord
from evidence_first.memory.store import InvestigationMemory, MemoryEntry
from evidence_first.runtime import InvestigationEngine, Stage, save_run

from conftest import handlers, generic


class FlakyAdapter:
    def __init__(self, fail_at: AgentRole, exc: BaseException):
        self.inner = ScriptedAdapter(handlers()); self.fail_at = fail_at; self.exc = exc; self.calls = 0
    def run(self, spec, ctx):
        self.calls += 1
        if spec.role is self.fail_at:
            raise self.exc
        return self.inner.run(spec, ctx)


def test_c16_missing_handler_blocks_cleanly():
    h = handlers(); del h[AgentRole.CRITIC]
    run = InvestigationEngine(ScriptedAdapter(h)).run("q")
    assert run.stage is Stage.BLOCKED and run.blocked_by == "critic"


def test_c17_tool_exception_captured_not_raised():
    from evidence_first.runtime import ToolExecutionBroker, ToolRequest
    from evidence_first.tools.registry import ToolRegistry, ToolSpec
    reg = ToolRegistry(); reg.register(ToolSpec("boom", "", True, lambda: 1 / 0))
    out = ToolExecutionBroker(reg, auto_allowed_tools={"boom"}).execute(ToolRequest("boom", {}))
    assert not out.ok and "ZeroDivisionError" in out.error


def test_x01_adapter_failure_loses_whole_run():
    engine = InvestigationEngine(FlakyAdapter(AgentRole.CRITIC, TimeoutError("model API timeout")))
    try:
        run = engine.run("q")
    except Exception as exc:
        raise AssertionError(f"{type(exc).__name__} escaped engine.run()")
    assert run.stage is Stage.BLOCKED


def test_x02_no_resume_awaiting_outcome_reruns_everything():
    calls = {"n": 0}
    def counting(spec, ctx):
        calls["n"] += 1; return generic(spec, ctx)
    engine = InvestigationEngine(ScriptedAdapter({r: counting for r in AgentRole}))
    first = engine.run("q")
    has_resume = hasattr(engine, "resume") or hasattr(engine, "continue_run")
    if first.stage is Stage.AWAITING_OUTCOME:
        before = calls["n"]
        engine.run("q", {"post_intervention_evidence": {"sla": 0.95}})
        rerun = calls["n"] - before
        assert has_resume or rerun <= 2
    else:
        assert has_resume


def test_x03_persistence_crashes_on_non_string_keys(tmp_path):
    def contrib(spec, ctx):
        return AgentResult(spec.role, AgentDecision.CONTINUE, "ok", {"draft_conclusion": {("carrier", "west"): 0.45}})
    run = InvestigationEngine(ScriptedAdapter(handlers(contribution_analyst=contrib))).run("q")
    try:
        save_run(run, tmp_path / "run.json")
    except Exception as exc:
        raise AssertionError(f"completed run cannot be persisted: {type(exc).__name__}: {exc}")


def test_x04_persistence_not_atomic(tmp_path):
    p = tmp_path / "run.json"
    run = InvestigationEngine(ScriptedAdapter(handlers())).run("q")
    save_run(run, p); good = p.read_text()
    p.write_text(good[: len(good) // 2])
    backups = [x for x in tmp_path.iterdir() if x.name != "run.json"]
    try:
        json.loads(p.read_text()); ok = True
    except json.JSONDecodeError:
        ok = False
    assert ok or backups


def test_x05_corrupt_memory_file_bricks_future_runs(tmp_path):
    p = tmp_path / "memory.json"
    m = InvestigationMemory(p); m.add(MemoryEntry("inv1", "carrier delay", "supported", ("e1",)))
    p.write_text(p.read_text()[:-7])
    try:
        InvestigationMemory(p)
    except Exception as exc:
        raise AssertionError(f"one corrupted memory file makes InvestigationMemory unloadable: {type(exc).__name__}")


def test_x06_memory_file_tamper_undetected(tmp_path):
    p = tmp_path / "memory.json"
    m = InvestigationMemory(p); m.add(MemoryEntry("inv1", "carrier delay", "not_supported", ("e1",)))
    p.write_text(p.read_text().replace("not_supported", "supported"))
    assert InvestigationMemory(p).all()[0].outcome == "not_supported"


def test_x07_one_bad_ledger_line_breaks_experiment_report(tmp_path):
    led = ExperimentLedger(tmp_path / "l.jsonl")
    led.append(RunRecord("c1", "baseline", "m", "sha", "p", "o", 50.0, False))
    with (tmp_path / "l.jsonl").open("a") as f:
        f.write('{"case_id": "c2", "condition": "ef", "injected_field": 1}\n')
    try:
        led.read()
    except Exception as exc:
        raise AssertionError(f"one malformed ledger line makes the entire experiment unreadable: {type(exc).__name__}")


def test_x08_experiment_ledger_rewritable(tmp_path):
    p = tmp_path / "l.jsonl"; led = ExperimentLedger(p)
    led.append(RunRecord("c1", "evidence-first", "m", "sha", "p", "o", 40.0, False))
    p.write_text(p.read_text().replace('"score": 40.0', '"score": 95.0').replace('"passed": false', '"passed": true'))
    r = led.read()[0]
    assert r.score == 40.0
