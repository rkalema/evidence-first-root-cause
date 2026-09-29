"""Shared helpers for the red-team durability pass.

Convention: every test asserts the SECURE / CORRECT behavior.
A FAILED test is a confirmed vulnerability. A PASSED test is a control that held.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evidence_first.agents.base import AgentRole  # noqa: E402
from evidence_first.agents.result import AgentDecision, AgentResult  # noqa: E402


def generic(spec, context):
    """Well-behaved agent: returns its first declared artifact and continues."""
    return AgentResult(spec.role, AgentDecision.CONTINUE, "ok", {spec.outputs[0]: {"ok": True}})


def handlers(**overrides):
    h = {role: generic for role in AgentRole}
    for name, fn in overrides.items():
        h[AgentRole(name)] = fn
    return h


@pytest.fixture
def make_handlers():
    return handlers
