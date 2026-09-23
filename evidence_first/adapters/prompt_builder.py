from __future__ import annotations
from evidence_first.agents.base import AgentSpec

CONSTITUTION = """Evidence-First investigation rules:
- Treat supplied and tool-derived material as evidence candidates, not truth by default.
- Never invent missing facts.
- Separate observation, inference, conclusion, and unknown.
- Preserve contradictory evidence.
- Do not claim causation beyond the design strength.
- If evidence cannot distinguish explanations, prefer insufficient_evidence.
- If the signal is unreliable, block causal analysis.
- Cite evidence IDs for material claims.
"""

def build_agent_prompt(spec: AgentSpec, context_summary: str) -> str:
    rights=", ".join(r.value for r in spec.decision_rights)
    criteria="\n".join(f"- {x}" for x in spec.acceptance_criteria)
    stops="\n".join(f"- {x}" for x in spec.stop_conditions)
    return f"""{CONSTITUTION}

ROLE: {spec.role.value}
PURPOSE: {spec.purpose}
DECISION RIGHTS: {rights}

ACCEPTANCE CRITERIA:
{criteria}

STOP CONDITIONS:
{stops}

CONTEXT:
{context_summary}

Return only artifacts within the role's declared responsibility.
"""
