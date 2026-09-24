from evidence_first.agents import AgentRole,DecisionRight,InvestigationOrchestrator,default_agent_registry

def test_registry_contains_all_agent_roles():
    assert set(default_agent_registry())==set(AgentRole)

def test_only_critic_can_approve_final_conclusion():
    r=default_agent_registry()
    a=[role for role,s in r.items() if DecisionRight.APPROVE_FINAL_CONCLUSION in s.decision_rights]
    assert a==[AgentRole.CRITIC]

def test_signal_and_data_quality_can_block():
    r=default_agent_registry()
    b={role for role,s in r.items() if DecisionRight.BLOCK_CAUSAL_ANALYSIS in s.decision_rights}
    assert AgentRole.SIGNAL_VALIDATOR in b and AgentRole.DATA_QUALITY_INVESTIGATOR in b

def test_hypothesis_generator_cannot_self_approve():
    assert DecisionRight.APPROVE_FINAL_CONCLUSION not in default_agent_registry()[AgentRole.HYPOTHESIS_GENERATOR].decision_rights

def test_orchestrator_order():
    roles=InvestigationOrchestrator().build_plan().roles()
    assert roles.index(AgentRole.SIGNAL_VALIDATOR)<roles.index(AgentRole.HYPOTHESIS_GENERATOR)
    assert roles.index(AgentRole.CONTRADICTION_INVESTIGATOR)<roles.index(AgentRole.CRITIC)
    assert roles.index(AgentRole.CONFOUND_REVIEWER)<roles.index(AgentRole.CONTRIBUTION_ANALYST)
    assert roles.index(AgentRole.CRITIC)<roles.index(AgentRole.INTERVENTION_PLANNER)

def test_blocking_agents():
    p=InvestigationOrchestrator().build_plan()
    b={t.role for t in p.tasks if t.blocking}
    assert {AgentRole.SIGNAL_VALIDATOR,AgentRole.DATA_QUALITY_INVESTIGATOR,AgentRole.CRITIC}<=b

def test_each_agent_has_contract():
    for s in default_agent_registry().values():
        assert s.stop_conditions and s.acceptance_criteria and s.required_inputs and s.outputs
