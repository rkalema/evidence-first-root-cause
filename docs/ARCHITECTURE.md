# Evidence-First System Architecture

## Product Thesis

Evidence-First is an evidence-governed investigation system for AI agents.

Its purpose is not to make an agent sound analytical. Its purpose is to force analytical claims to remain traceable to evidence, expose contradictions, preserve uncertainty, and define what would falsify the current conclusion.

The first flagship capability is `evidence-first-root-cause`.

## Core Pipeline

```text
Incident / Question
        ↓
Evidence Intake
        ↓
Signal Validator
        ↓
Evidence Ledger
        ↓
Hypothesis Engine
        ↓
Investigation Planner
        ↓
Tools / SQL / Python / APIs
        ↓
Contradiction + Falsification
        ↓
Confound / Causal Review
        ↓
Contribution Analysis
        ↓
Critic
        ↓
Conclusion + Confidence
        ↓
Recommended Intervention
        ↓
Human Approval
        ↓
Outcome Measurement
        ↓
Investigation Memory
```

## Non-Negotiable Architecture Rules

1. Evidence is immutable after ingestion. Corrections create a new evidence record.
2. Every material claim must link to one or more evidence records or be labeled unknown.
3. Observations, inferences, conclusions, and unknowns are distinct types.
4. A hypothesis cannot be promoted without both supporting and disconfirming checks.
5. Contradictory evidence is preserved, not summarized away.
6. Confidence is derived from evidence quality and test coverage, not model tone.
7. Tool outputs are evidence candidates, never automatically conclusions.
8. High-impact external actions require explicit approval.
9. Model providers are replaceable; investigation state is not stored in model conversation history.
10. An investigation may terminate as `insufficient_evidence` or `data_quality_blocked`.
