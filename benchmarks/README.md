# Benchmark Laboratory

The repository currently contains **20 adversarial cases** across operations, supply chain, customer analytics, healthcare operations, program performance, and AI/data incidents.

## Evaluation rule

Models receive only:

- `prompt`
- `facts`

They never receive the `expected` scoring key.

## Controlled comparison

For matched baseline-versus-Evidence-First experiments:

1. use the same model and configuration;
2. use fresh contexts;
3. keep the user incident/evidence identical;
4. vary only the Evidence-First method layer;
5. preserve raw outputs;
6. validate schema before scoring;
7. report every run, including failures;
8. record cost/latency/tool calls when available.

Prepare matched prompt packets:

```bash
python scripts/evaluate_runner.py prepare price-vs-stockout --out runs
```

Score and compare:

```bash
python scripts/evaluate_runner.py score price-vs-stockout result.json
python scripts/evaluate_runner.py compare price-vs-stockout baseline.json evidence-first.json
```

For a multi-case study, create a manifest with entries containing `case_id`, `baseline`, and `evidence_first`, then run:

```bash
python scripts/evaluate_runner.py suite manifest.json
```

The benchmark tests evidence discipline against encoded cases. It does not by itself establish universal scientific validity.
