from .base import AgentRole,AgentSpec,DecisionRight

def default_agent_registry():
    S=[]
    def add(role,purpose,inputs,outputs,rights,stops,criteria):
        S.append(AgentSpec(role,purpose,tuple(inputs),tuple(outputs),tuple(rights),tuple(stops),tuple(criteria)))

    add(AgentRole.EVIDENCE_INTAKE_COORDINATOR,
        "Normalize source material into provenance-preserving evidence candidates without interpreting cause.",
        ["problem_statement","source_inventory"],
        ["intake_manifest","evidence_candidates","intake_issues","available_evidence_inventory","source_metadata","evidence_ledger"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.ADD_EVIDENCE],
        ["source cannot be parsed","provenance cannot be established"],
        ["every source is fingerprinted","raw source instructions are treated as data","no causal claims are created during intake"])

    add(AgentRole.INVESTIGATION_PLANNER,
        "Translate an incident into a bounded investigation plan without deciding the root cause.",
        ["problem_statement","available_evidence_inventory"],
        ["investigation_plan","required_data","stop_conditions"],
        [DecisionRight.READ_EVIDENCE],
        ["required evidence cannot be accessed"],
        ["plan validates signal first","plan includes competing explanations","plan defines insufficient-evidence stop"])

    add(AgentRole.SIGNAL_VALIDATOR,
        "Determine whether the observed anomaly is trustworthy enough for causal investigation.",
        ["problem_statement","evidence_ledger"],
        ["signal_validation_result","validated_signal","validation_checks","blocking_reason"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.BLOCK_CAUSAL_ANALYSIS],
        ["signal is unreliable","critical denominator or instrumentation integrity unresolved"],
        ["checks denominator/definition integrity","distinguishes missing validation from validity","blocks when signal cannot be trusted"])

    add(AgentRole.DATA_QUALITY_INVESTIGATOR,
        "Investigate missingness, duplication, schema, joins, freshness, lineage, and source integrity.",
        ["evidence_ledger","source_metadata"],
        ["data_quality_findings","quality_evidence","blocking_reason"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.ADD_EVIDENCE,DecisionRight.BLOCK_CAUSAL_ANALYSIS],
        ["material data defect invalidates signal"],
        ["findings trace to source","absence of error is not proof","unresolved risks recorded"])

    add(AgentRole.HYPOTHESIS_GENERATOR,
        "Generate competing explanations and specify distinguishing evidence.",
        ["validated_signal","evidence_ledger"],
        ["hypotheses","expected_evidence","disconfirming_evidence","required_data"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.ADD_HYPOTHESIS],
        ["signal validation has not passed"],
        ["multiple hypotheses where possible","data-quality hypothesis when relevant","falsifiable expectations"])

    add(AgentRole.EVIDENCE_ANALYST,
        "Use read-only analytical tools to test hypotheses and return traceable derived evidence.",
        ["hypotheses","evidence_ledger","tool_registry"],
        ["analysis_results","derived_evidence","segmentation_results","hypothesis_tests","method_limits"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.ADD_EVIDENCE,DecisionRight.RUN_ANALYTICAL_TOOL],
        ["required tool or data unavailable"],
        ["tool outputs retain source provenance","methods are reproducible","analysis does not silently become a conclusion"])

    add(AgentRole.CONTRADICTION_INVESTIGATOR,
        "Actively search for evidence that weakens or falsifies leading hypotheses.",
        ["hypotheses","evidence_ledger"],
        ["contradiction_findings","counterexamples","surviving_hypotheses"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.CHALLENGE_HYPOTHESIS],
        ["no hypothesis has enough support to challenge"],
        ["tests predicted presence/absence","preserves contradictions","does not promote by elimination alone"])

    add(AgentRole.CONFOUND_REVIEWER,
        "Detect common causes, selection effects, mix shifts, denominator changes, and overlapping attribution.",
        ["hypotheses","evidence_ledger","segmentation_results"],
        ["confound_findings","adjustment_requests","causal_design_limitations"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.CLASSIFY_CONFOUND],
        ["required segmentation unavailable"],
        ["separates composition from within-group change","flags double counting","states observational limits"])

    add(AgentRole.CONTRIBUTION_ANALYST,
        "Quantify contribution and impact without unsupported precision or double counting.",
        ["surviving_hypotheses","evidence_ledger","confound_findings"],
        ["contribution_estimates","impact_estimates","precision_limits","draft_conclusion"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.QUANTIFY_CONTRIBUTION],
        ["evidence cannot support numerical attribution"],
        ["separates measured from estimated","does not sum overlapping contributions","uses unknown instead of fabricated precision"])

    add(AgentRole.CRITIC,
        "Independently test whether the investigation earned its proposed conclusion.",
        ["draft_conclusion","evidence_ledger","hypothesis_tests","confound_findings"],
        ["critic_verdict","unsupported_claims","required_revisions","critic_approved_conclusion"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.CHALLENGE_HYPOTHESIS,DecisionRight.APPROVE_FINAL_CONCLUSION],
        ["material claim lacks evidence","contradiction review incomplete"],
        ["rejects unsupported claims","checks omitted contradictions","can force insufficient_evidence"])

    add(AgentRole.INTERVENTION_PLANNER,
        "Convert supported mechanisms into reversible actions and measurable validation plans.",
        ["critic_approved_conclusion","evidence_ledger"],
        ["containment","corrective_action","preventive_action","validation_plan"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.RECOMMEND_ACTION],
        ["no critic-approved mechanism exists"],
        ["action tied to mechanism","defines target/baseline/comparison/timing/success","defines rollback/escalation"])

    add(AgentRole.OUTCOME_EVALUATOR,
        "Evaluate whether the intervention changed the target metric as predicted and whether the causal explanation survived.",
        ["validation_plan","post_intervention_evidence"],
        ["outcome_assessment","causal_update","followup_required"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.EVALUATE_OUTCOME],
        ["post-intervention evidence unavailable"],
        ["compares against declared baseline","uses declared success criteria","reopens investigation when prediction fails"])

    add(AgentRole.MEMORY_CURATOR,
        "Store reusable investigation lessons without converting prior conclusions into current evidence.",
        ["critic_approved_conclusion","outcome_assessment"],
        ["memory_entries"],
        [DecisionRight.READ_EVIDENCE,DecisionRight.WRITE_MEMORY],
        ["investigation is not complete"],
        ["stores decisive evidence ids","records disproven hypotheses","marks memory as context not evidence"])

    R={s.role:s for s in S}
    if len(R)!=len(S): raise ValueError("duplicate agent role")
    return R
