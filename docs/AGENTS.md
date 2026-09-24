# Evidence-First Agent Architecture

Evidence-First uses specialized investigators with constrained responsibilities over one shared evidence ledger. Agents are not personalities and do not vote on truth.

## Complete initial agent set

1. Evidence Intake Coordinator
2. Investigation Planner
3. Signal Validator
4. Data Quality Investigator
5. Hypothesis Generator
6. Evidence Analyst
7. Contradiction / Falsification Investigator
8. Confound Reviewer
9. Contribution Analyst
10. Critic
11. Intervention Planner
12. Outcome Evaluator
13. Memory Curator

## Governance

Every agent declares required inputs, outputs, decision rights, stop conditions, and acceptance criteria.

Key controls:
- Evidence Intake can stop on unreadable or untraceable sources.
- Signal Validation and Data Quality can block causal analysis.
- Hypothesis Generator cannot approve its own conclusion.
- Evidence Analyst may run analytical tools but may not certify causation.
- Contradiction search runs before final critique.
- Confound review runs before numerical contribution analysis.
- Critic is the only analytical role allowed to approve a final causal conclusion.
- Intervention Planner recommends actions but does not approve causation.
- Outcome Evaluator checks whether intervention predictions came true.
- Memory Curator stores lessons as context, never as new evidence.

## Model independence

Agent contracts are code-level objects rather than provider-specific prompt text. Claude, Codex, and future harnesses can execute the same governed tasks through adapters.

## Two-phase lifecycle

An investigation can reach an intervention plan before outcome evidence exists. The runtime then pauses at `awaiting_outcome`. Once post-intervention evidence is supplied, the Outcome Evaluator and Memory Curator complete the lifecycle.
