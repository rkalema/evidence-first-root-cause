# Contributing

Contributions that improve analytical discipline are welcome.

## Good contributions

Especially useful contributions include:

- adversarial examples where a plausible explanation is wrong
- cases where a data-quality defect mimics a business problem
- examples with multiple contributing causes
- examples with strong contradictory evidence
- new evaluation fixtures
- clearer falsification tests
- domain extensions that preserve the core evidence discipline

## Pull requests

A pull request should explain:

1. what analytical failure or use case it addresses;
2. why the change belongs in the core skill rather than a domain extension;
3. how the behavior is tested;
4. whether it changes the output schema.

Run before submission:

```bash
python -m pip install -r requirements-dev.txt
pytest -q
python scripts/validate_output.py tests/fixtures/valid_supported.json
```

## Design rule

Do not make the skill more certain merely to make outputs sound more decisive.

`insufficient_evidence` and `data_quality_blocked` are valid outcomes.
