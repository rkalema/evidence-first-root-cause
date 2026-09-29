# Changelog

All notable changes to this project will be documented here.

## Unreleased — Evidence-First system build candidate

### Added

- Evidence-First governed investigation architecture
- 13 governed agent roles with decision rights, stop conditions, and acceptance criteria
- evidence ledger, typed claims, hypothesis registry, contradiction review, and explicit stop states
- CSV, JSON, text, and Excel evidence intake with source fingerprints and provenance
- deterministic investigation runtime with intervention/outcome two-phase lifecycle
- read-only DataFrame, statistics, and SQL analytical tools
- derived-evidence provenance
- human-approval governance for high-impact/external write actions
- prompt-injection source boundaries
- investigation memory that remains context rather than evidence
- six domain packs
- 20 adversarial benchmark cases
- matched baseline-vs-Evidence-First evaluation runner
- aggregate evaluation metrics and ablation plan
- reproducibility, research, methodology, threat-model, and limitations documentation
- real-data pipeline demonstration
- Claude and Codex integration guidance
- installable Python package and expanded CLI
- expanded automated tests

No behavioral-improvement numbers are claimed until the controlled evaluation is run.

## Initial public skill

### Added

- Initial public `SKILL.md`
- Twelve-stage evidence-first root-cause workflow
- Explicit observation/inference/conclusion/unknown evidence classes
- Competing-hypothesis and contradictory-evidence requirements
- JSON Schema for structured outputs
- Output validation script
- Valid and invalid test fixtures
- Automated GitHub Actions test workflow
- Healthcare, operations, and supply-chain usage examples
