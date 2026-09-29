# Professor Demo Path

Evidence-First is designed so a reviewer can experience the system without Richard or another developer guiding the session.

## Five-minute path

```bash
git clone https://github.com/rkalema/evidence-first-root-cause
cd evidence-first-root-cause
python -m pip install -e .
efrc doctor
efrc demo
```

The bundled demo is deterministic and does not require an external model account. It exercises the governed lifecycle and writes an auditable workspace with the investigation report, evidence ledger, hypotheses, audit trail, result, and manifest.

## Investigate your own evidence

Configure a provider once:

```bash
efrc init
```

Then supply a question and one or more evidence files:

```bash
efrc investigate \
  --question "Why did the operational metric deteriorate?" \
  --source evidence.xlsx
```

Supported inputs include CSV, JSON, text/Markdown, XLSX, and XLSM. The output is written into a timestamped run workspace.

## Review the system

After the demo:

1. Read `README.md` and `docs/ARCHITECTURE.md`.
2. Inspect the governed agent contracts in `evidence_first/agents/`.
3. Inspect evidence intake, the ledger, read-only tools, runtime governance, memory, and domain packs.
4. Review the red-team durability suite in `redteam/`.
5. Run `pytest -q`.
6. Review `docs/RESEARCH_PROTOCOL.md`, reproducibility controls, threat model, ethics, and limitations.
7. Run controlled baseline-vs-Evidence-First comparisons only after confirming the benchmark gold keys are isolated from the model context.

The project is intended to be evaluated simultaneously as software, analytical methodology, and research artifact.
