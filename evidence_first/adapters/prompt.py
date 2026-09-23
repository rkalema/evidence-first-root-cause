from __future__ import annotations
import json
from evidence_first.agents.base import AgentSpec

def render_agent_prompt(spec:AgentSpec, context:dict[str,object])->str:
    return "\n".join([
        f"ROLE: {spec.role.value}",
        f"PURPOSE: {spec.purpose}",
        "DECISION RIGHTS: "+", ".join(r.value for r in spec.decision_rights),
        "STOP CONDITIONS: "+json.dumps(spec.stop_conditions),
        "ACCEPTANCE CRITERIA: "+json.dumps(spec.acceptance_criteria),
        "CONTEXT:",
        json.dumps(context,indent=2,default=str),
        "Return only artifacts permitted by the contract. Preserve uncertainty and cite evidence identifiers."
    ])
