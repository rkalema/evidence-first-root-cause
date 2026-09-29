from evidence_first.agents.artifacts import validate_artifact_flow
from evidence_first.agents.orchestrator import InvestigationOrchestrator

def test_governed_artifact_flow_is_closed():
    assert validate_artifact_flow(InvestigationOrchestrator().build_plan())==()
