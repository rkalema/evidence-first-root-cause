from __future__ import annotations
from dataclasses import dataclass
from .base import AgentSpec
from .result import AgentResult

@dataclass(frozen=True)
class ContractViolation:
    code:str
    message:str

def validate_agent_result(spec:AgentSpec,result:AgentResult)->tuple[ContractViolation,...]:
    problems=[]
    if result.role is not spec.role:
        problems.append(ContractViolation('wrong_role',f'expected {spec.role.value}, got {result.role.value}'))
    undeclared=sorted(set(result.artifacts)-set(spec.outputs))
    if undeclared:
        problems.append(ContractViolation('undeclared_artifact','undeclared artifact(s): '+', '.join(undeclared)))
    if not result.summary.strip():
        problems.append(ContractViolation('empty_summary','agent result summary cannot be empty'))
    return tuple(problems)
