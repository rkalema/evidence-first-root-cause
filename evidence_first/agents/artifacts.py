from __future__ import annotations
from dataclasses import dataclass
from .orchestrator import InvestigationPlan
from .catalog import default_agent_registry

EXTERNAL_INPUTS={'problem_statement','source_inventory','post_intervention_evidence','tool_registry'}

@dataclass(frozen=True)
class ArtifactGap:
    role:str
    artifact:str

def validate_artifact_flow(plan:InvestigationPlan)->tuple[ArtifactGap,...]:
    registry=default_agent_registry(); available=set(EXTERNAL_INPUTS); gaps=[]
    for task in plan.tasks:
        spec=registry[task.role]
        for req in spec.required_inputs:
            if req not in available: gaps.append(ArtifactGap(task.role.value,req))
        available.update(spec.outputs)
    return tuple(gaps)
