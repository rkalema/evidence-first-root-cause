# Evidence-First Root Cause

> **Stop AI from making up plausible root causes.**

AI systems are excellent at explanations. They are not automatically good at proving that an explanation is supported.

**Evidence-First Root Cause** is a reusable agent skill and evaluation toolkit that forces an AI system to validate the signal, test competing explanations, search for contradicting evidence, preserve uncertainty, and define how an intervention will be measured.

## What makes this different

This is not a prompt collection.

The repository includes:

- a portable `SKILL.md`
- a strict JSON output contract
- schema validation
- adversarial benchmark scenarios
- a deterministic benchmark scorer
- CLI commands for validation and evaluation
- positive and negative tests
- cross-domain examples
- CI checks

The skill explicitly permits the correct answer to be:

- `insufficient_evidence`
- `data_quality_blocked`
- `multiple_contributors_supported`

That is intentional. A system that always finds a neat root cause is not trustworthy.

## The method

```text
Validate signal
    ↓
Establish baseline
    ↓
Localize anomaly
    ↓
Generate competing hypotheses
    ↓
Test evidence
    ↓
Seek contradictions
    ↓
Quantify contribution
    ↓
Separate observation / inference / conclusion
    ↓
Assign confidence
    ↓
Recommend action
    ↓
Measure the intervention
```

## Install as an agent skill

Clone or copy this repository into the skill directory used by your agent environment.

Claude Code:

```text
.claude/skills/evidence-first-root-cause/
```

GitHub Copilot repository skills:

```text
.github/skills/evidence-first-root-cause/
```

Keep the repository files together so the schema, benchmark cases, and evaluator remain available.

## CLI

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Validate a structured agent output:

```bash
python efrc.py validate path/to/result.json
```

List benchmark cases:

```bash
python efrc.py cases
```

Score an agent output against a benchmark:

```bash
python efrc.py score benchmarks/cases/data-quality-denominator.json path/to/result.json
```

Run repository tests:

```bash
pytest -q
```

## Behavioral benchmarks

The included cases are intentionally designed to catch common analytical failures:

| Case | Trap |
|---|---|
| `price-vs-stockout` | obvious correlation hides stockout |
| `absenteeism-confounder` | two variables share a common cause |
| `data-quality-denominator` | apparent performance spike is a broken denominator |
| `multiple-contributors` | no single cause explains the deterioration |
| `insufficient-evidence` | agent must refuse to manufacture certainty |
| `contradictory-supplier` | attractive supplier story conflicts with unaffected sites |

The benchmark scorer checks whether an agent:

- chooses the correct evidence status
- validates the signal
- tests enough competing hypotheses
- surfaces required contradictions
- avoids prohibited causal claims
- uses an appropriate evidence class
- calibrates confidence
- supplies a real intervention-validation plan

## Example

**Question**

> Fulfillment SLA fell from 94% to 79%. Why?

A weak answer might say:

> Supplier delays and staffing shortages likely caused the decline.

Evidence-First Root Cause instead requires the agent to determine whether the metric is valid, localize the deterioration, test supplier delay and staffing against alternatives, inspect unaffected comparison sites, and separate what is observed from what is inferred.

If the evidence cannot distinguish the causes, the correct result is `insufficient_evidence`.

## Repository map

```text
SKILL.md
README.md
DESIGN.md
SECURITY.md
efrc.py
schemas/
scripts/
benchmarks/
tests/
examples/
.github/workflows/
```

## Design boundary

The toolkit evaluates **evidence discipline**, not scientific truth by itself.

A passing score means the response followed the expected analytical controls for that benchmark. It does not make poor underlying data, invalid experimental design, or fabricated source evidence trustworthy.

See [`DESIGN.md`](DESIGN.md).

## License

Apache License 2.0.
