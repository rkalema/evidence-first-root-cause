from dataclasses import dataclass
from .base import AgentRole,AgentTask
from .catalog import default_agent_registry

@dataclass(frozen=True)
class InvestigationPlan:
    tasks: tuple[AgentTask,...]
    def roles(self): return tuple(t.role for t in self.tasks)

class InvestigationOrchestrator:
    def __init__(self): self.registry=default_agent_registry()
    def build_plan(self):
        order=(AgentRole.INVESTIGATION_PLANNER,AgentRole.SIGNAL_VALIDATOR,AgentRole.DATA_QUALITY_INVESTIGATOR,AgentRole.HYPOTHESIS_GENERATOR,AgentRole.CONTRADICTION_INVESTIGATOR,AgentRole.CONFOUND_REVIEWER,AgentRole.CONTRIBUTION_ANALYST,AgentRole.CRITIC,AgentRole.INTERVENTION_PLANNER)
        blocking={AgentRole.SIGNAL_VALIDATOR,AgentRole.DATA_QUALITY_INVESTIGATOR,AgentRole.CRITIC}
        return InvestigationPlan(tuple(AgentTask(r,self.registry[r].purpose,self.registry[r].required_inputs,r in blocking) for r in order))
