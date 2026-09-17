# Evidence-First Root Cause

**A reusable root-cause analysis skill for AI agents that tests evidence before it tells a story.**

AI systems are very good at producing plausible explanations. Plausible is not the same as supported.

`evidence-first-root-cause` gives an agent a disciplined investigation workflow:

**Validate signal → establish baseline → localize anomaly → generate competing hypotheses → test evidence → search for contradictions → quantify impact → classify certainty → recommend action → measure intervention**

## Why this exists

A typical AI root-cause answer can fail in predictable ways:

- it explains a bad metric before checking whether the metric is trustworthy;
- it treats correlation as causation;
- it anchors on the first plausible story;
- it ignores contradicting evidence;
- it gives false precision;
- it recommends action without defining how success will be measured.

This skill is designed to make those failures harder.

## What it can analyze

The core method is domain-neutral and can be applied to:

- business and operational KPIs
- healthcare operations
- claims and revenue-cycle analysis
- supply-chain disruptions
- program performance
- product metrics
- customer retention
- data-quality incidents
- AI/model performance
- workflow failures

## Repository structure

```text
evidence-first-root-cause/
├── SKILL.md
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── schemas/
│   └── root_cause_output.schema.json
├── scripts/
│   └── validate_output.py
├── tests/
│   ├── test_validate_output.py
│   └── fixtures/
│       ├── valid_supported.json
│       ├── valid_insufficient.json
│       └── invalid_missing_evidence.json
├── examples/
│   ├── healthcare-claims.md
│   ├── operations.md
│   └── supply-chain.md
└── .github/
    └── workflows/
        └── test.yml
```

## Install as an agent skill

Agent-skill clients differ in where they discover skills. The portable unit is this repository folder containing `SKILL.md`.

For Claude Code, copy or clone the skill into your project's skills directory:

```text
.claude/skills/evidence-first-root-cause/
```

For GitHub Copilot projects using repository skills:

```text
.github/skills/evidence-first-root-cause/
```

Keep `SKILL.md`, `schemas/`, and any supporting files together.

## Minimal usage

Ask the agent something like:

> Our fulfillment SLA dropped from 94% to 79% this month. Use evidence-first-root-cause. Do not assume the reason. Tell me what data you need, test competing explanations, and separate observations from conclusions.

Or:

> Claim denials rose sharply last week. Apply evidence-first-root-cause and return the structured JSON format.

## Structured output

The repository includes a JSON Schema for machine-consumable results:

```text
schemas/root_cause_output.schema.json
```

Validate an output:

```bash
python scripts/validate_output.py result.json
```

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest -q
```

## Design philosophy

This skill deliberately allows the correct answer to be:

> **Insufficient evidence.**

That is a feature, not a failure.

The goal is not to force every anomaly into a neat narrative. The goal is to help an agent identify the strongest explanation the evidence can actually support and make the uncertainty visible.

## Roadmap

Planned domain extensions include:

- healthcare root cause
- supply-chain root cause
- workforce-operations root cause
- program-performance root cause

The core evidence discipline will remain stable across extensions.

## Contributing

Contributions are welcome, especially:

- adversarial test cases
- examples where correlation is easily mistaken for causation
- domain adaptations
- improved falsification checks
- evaluation datasets

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Apache License 2.0.
