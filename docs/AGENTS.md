# Evidence-First Agent Architecture

Evidence-First uses specialized investigators with constrained responsibilities over one shared evidence ledger. Agents are not personalities and do not vote on truth.

## Initial agent set

1. Investigation Planner
2. Signal Validator
3. Data Quality Investigator
4. Hypothesis Generator
5. Contradiction/Falsification Investigator
6. Confound Reviewer
7. Contribution Analyst
8. Critic
9. Intervention Planner

## Governance

Each agent has required inputs, allowed outputs, decision rights, stop conditions, and acceptance criteria. Signal validation and data quality can block causal analysis. The Hypothesis Generator cannot approve its own conclusion. The Critic is the only initial analytical agent allowed to approve a final conclusion. Intervention planning occurs only after critic approval.

## Model independence

The contracts are code-level objects rather than provider-specific prompt text. Claude, Codex, and future harnesses can execute the same governed tasks through adapters.
