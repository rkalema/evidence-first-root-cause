# Architecture Diagram

Incident and source data
  -> Evidence Intake Coordinator
  -> Evidence Ledger
  -> Investigation Planner
  -> Signal Validator
  -> Data Quality Investigator
  -> Hypothesis Generator
  -> Evidence Analyst + read-only tools
  -> Contradiction / Falsification Investigator
  -> Confound Reviewer
  -> Contribution Analyst
  -> Critic
  -> Intervention Planner
  -> Human approval where required
  -> Outcome Evaluator
  -> Memory Curator

Cross-cutting controls: source fingerprints, untrusted-content boundaries, decision rights, audit events, domain packs, benchmark evaluation, and reproducibility metadata.
