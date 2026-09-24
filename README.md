# Evidence-First

> **Make AI prove its explanation before a human acts on it.**

Evidence-First is an **evidence-governed investigation system for AI agents**. It is designed to reduce unsupported causal conclusions by forcing agents to validate signals, preserve source provenance, test competing hypotheses, search for contradictions, review confounding, quantify only what the evidence supports, and measure whether an intervention actually worked.

The flagship capability is **Evidence-First Root Cause**.

## Why this exists

LLMs are very good at producing plausible explanations. Plausibility is not evidence.

Evidence-First separates investigation responsibilities across governed agents and keeps the analytical state outside model conversation history. A model can propose an explanation, but it cannot silently promote that explanation into a conclusion without passing the system's evidence controls.

Correct outcomes explicitly include:

- `root_cause_supported`
- `multiple_contributors_supported`
- `insufficient_evidence`
- `data_quality_blocked`

A system that always finds a neat cause is not trustworthy.

## System architecture

```text
Incident + source data
        ↓
Evidence Intake Coordinator
        ↓
Evidence Ledger + provenance
        ↓
Investigation Planner
        ↓
Signal Validator
        ↓
Data Quality Investigator
        ↓
Hypothesis Generator
        ↓
Evidence Analyst + read-only tools
        ↓
Contradiction / Falsification Investigator
        ↓
Confound Reviewer
        ↓
Contribution Analyst
        ↓
Critic
        ↓
Intervention Planner
        ↓
Human approval where required
        ↓
Outcome Evaluator
        ↓
Memory Curator
```

The model provider is replaceable. The investigation state, evidence ledger, governance rules, and evaluation protocol are not.

## Governed agents

Evidence-First currently defines 13 first-class agent roles:

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

Every role declares required inputs, allowed outputs, decision rights, stop conditions, and acceptance criteria. The Hypothesis Generator cannot approve its own conclusion. Signal Validation and Data Quality can block causal analysis. The Critic is the only analytical role permitted to approve the final causal conclusion.

## Evidence intake

Supported initial source formats:

- CSV
- JSON
- plain text
- Excel (.xlsx/.xlsm)

Sources receive SHA-256 fingerprints and row-level provenance. Intake detects malformed inputs, empty sources, duplicate headers, duplicate rows, and missing values. Parsing success is never treated as proof that the data is valid.

## Analytical tools

The initial read-only analytical layer includes:

- DataFrame profiling
- grouped metrics
- before/after comparisons
- correlations
- deterministic difference, weighted-mean, and slope utilities
- read-only SQL queries
- provenance conversion of derived analytical results into evidence records

Tool outputs are evidence candidates, not conclusions.

## Domain packs

Initial domain packs cover:

- operations
- supply chain
- customer analytics
- healthcare operations
- AI/data incidents
- program performance

Domain packs add domain metrics, common confounders, validation checks, and cautions without weakening the core evidence rules.

## Investigation memory

Evidence-First can persist completed investigation lessons, including disproven hypotheses, decisive evidence IDs, and intervention outcomes.

Memory is **context, not evidence**. A previous conclusion cannot automatically become evidence in a new investigation.

## Evaluation laboratory

The repository includes **20 adversarial benchmark cases** spanning multiple domains.

The deterministic scorer evaluates:

- correct analysis status
- signal validation
- competing hypotheses
- required evidence
- avoidance of prohibited causal conclusions
- evidence classification
- confidence calibration
- intervention validation

The controlled evaluation runner generates matched baseline and Evidence-First prompts while keeping gold expectations hidden from the model.

```bash
python scripts/evaluate_runner.py prepare price-vs-stockout --out runs
python scripts/evaluate_runner.py score price-vs-stockout result.json
python scripts/evaluate_runner.py compare price-vs-stockout baseline.json evidence-first.json
```

The research protocol also defines ablations that remove signal validation, contradiction search, confound review, and critic stages to determine which components actually matter.

**No benchmark improvement numbers are claimed until the controlled study is run.**

## Research question

The project is designed to support empirical study of questions such as:

> Does evidence-governed investigation reduce unsupported causal conclusions and improve traceability, contradiction detection, uncertainty calibration, and falsification behavior relative to an unstructured LLM baseline?

Primary outcomes include false causal conclusion rate, correct insufficient-evidence rate, correct data-quality-stop rate, contradiction detection, confound detection, evidence traceability, intervention falsifiability, elapsed time, model cost, and tool calls.

## Quick start

```bash
python -m pip install -e .
pytest -q
python efrc.py cases
python efrc.py domains
python efrc.py ablations
```

Inspect an evidence source:

```bash
python efrc.py intake path/to/data.csv
```

Run the real-data pipeline demonstration:

```bash
python examples/end_to_end_demo.py
```

Validate a canonical structured investigation output:

```bash
python efrc.py validate result.json
```

Score it against a benchmark:

```bash
python efrc.py score benchmarks/cases/data-quality-denominator.json result.json
```

## Agent integrations

Claude Code:

```text
.claude/skills/evidence-first-root-cause/
```

Codex and other harnesses can execute the same governed `AgentSpec` contracts through adapters. See `integrations/`.

## Repository map

```text
SKILL.md                         flagship portable skill
evidence_first/agents/           governed agent contracts
evidence_first/intake/           source parsing + fingerprints
evidence_first/core/             evidence ledger + hypotheses
evidence_first/runtime/          investigation execution
evidence_first/tools/            read-only analytical tools
evidence_first/governance/       approval controls
evidence_first/memory/           investigation memory
evidence_first/domains/          domain packs
evidence_first/evaluation/       aggregate metrics + ablations
evidence_first/connectors/       source connector contracts
evidence_first/reporting/        investigation reports
schemas/                         machine-readable contracts
benchmarks/                      adversarial evaluation corpus
scripts/                         validators, scorer, runner, installer
examples/                        real-data demonstration
docs/                            architecture, methodology, research protocol
tests/                           regression and governance tests
```

## Research and design documentation

Start with:

- `docs/ARCHITECTURE.md`
- `docs/AGENTS.md`
- `docs/METHODOLOGY.md`
- `docs/RESEARCH_PROTOCOL.md`
- `docs/REPRODUCIBILITY.md`
- `docs/THREAT_MODEL.md`
- `docs/LIMITATIONS.md`
- `docs/PROFESSOR_DEMO.md`

## Security and governance

External source content is untrusted evidence data, never agent instruction. Analytical tools are read-only by default. High-impact or external write actions require explicit human approval. Benchmark gold expectations are kept outside model context.

## Design boundary

Evidence-First is not a causal-inference engine, proof that an LLM conclusion is true, a substitute for valid data collection, or an autonomous authority for consequential decisions.

It is a system for making AI investigations **more explicit, traceable, falsifiable, and difficult to bluff**.

## License

Apache License 2.0.
