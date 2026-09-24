from evidence_first.agents.base import AgentRole
from evidence_first.agents.catalog import default_agent_registry
from evidence_first.agents.result import AgentDecision,AgentResult
from evidence_first.agents.validation import validate_agent_result

def test_undeclared_artifact_rejected():
    spec=default_agent_registry()[AgentRole.SIGNAL_VALIDATOR]
    r=AgentResult(spec.role,AgentDecision.CONTINUE,'ok',{'root_cause':'invented'})
    v=validate_agent_result(spec,r)
    assert any(x.code=='undeclared_artifact' for x in v)

def test_declared_artifact_allowed():
    spec=default_agent_registry()[AgentRole.SIGNAL_VALIDATOR]
    r=AgentResult(spec.role,AgentDecision.CONTINUE,'ok',{'signal_validation_result':{'trustworthy':True}})
    assert not validate_agent_result(spec,r)
