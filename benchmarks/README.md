# Behavioral Benchmarks

These cases are designed to test whether an agent follows evidence-first reasoning under common analytical traps.

## Important

When evaluating a model, provide only:

- `prompt`
- `facts`

Do **not** reveal the `expected` section to the model. It is the scoring key.

## Run

```bash
python efrc.py cases
python efrc.py score benchmarks/cases/data-quality-denominator.json result.json
```

A result must first pass the canonical output schema. The benchmark scorer then checks explicit behavior expected for the case.

The benchmark is intentionally deterministic and reproducible. It does not claim to prove scientific correctness beyond the facts encoded in each case.
