# Empirical Validation Protocol

## Objective

Measure whether Evidence-First improves evidence-grounded causal investigation relative to a matched unstructured baseline, without exposing benchmark gold answers during generation.

## Frozen study design

- Corpus: 20 adversarial benchmark cases.
- Conditions: baseline and Evidence-First.
- Repetitions: 3 per case and condition by default.
- Total planned matched generations: 120.
- Same model and provider within a study.
- Same evidence and output contract across paired conditions.
- Fresh model context for every trial.
- Deterministic randomized execution order from a recorded seed.
- Gold expectations remain unavailable to the inference step.
- Raw model output is saved before scoring.
- Failed, malformed, and missing runs remain visible in the study record.

## Primary outcomes

1. False causal conclusion rate.
2. Mean and median benchmark score.
3. Correct insufficient-evidence decisions.
4. Correct data-quality-block decisions.
5. Pass rate.
6. Schema-valid output rate.

## Efficiency outcomes

- input tokens
- output tokens
- wall-clock latency
- provider request ID when available
- tool calls where applicable
- estimated monetary cost only when a dated provider price table is explicitly supplied; the repository does not hard-code volatile model prices

## Paired statistical analysis

The study reports paired Evidence-First minus baseline score deltas for each case/repetition pair, wins/ties/losses, an exact two-sided sign test, and a deterministic bootstrap 95% confidence interval for the mean paired score delta.

These statistics describe this benchmark sample. They do not establish broad scientific generality.

## Ablation plan

After the matched baseline study is complete, run:

- full system
- no signal validation
- no contradiction search
- no confound review
- no critic

Ablation prompt generation removes the targeted instruction while preserving the remainder of the Evidence-First method. Runtime ablations should be reported separately from prompt-only ablations.

## Reproducibility controls

Every prepared trial records:

- case ID
- condition
- repetition
- randomized order
- exact prompt path
- SHA-256 of the prompt
- repository commit SHA
- provider
- model
- study seed

Each output records a SHA-256 after inference. The study manifest is verified before scoring.

## Execution

Prepare:

```bash
python scripts/empirical_study.py prepare \
  --out studies/gpt-study \
  --provider openai \
  --model MODEL_NAME \
  --repetitions 3
```

Run:

```bash
python scripts/empirical_study.py run studies/gpt-study
```

Score only after inference is complete:

```bash
python scripts/empirical_study.py score studies/gpt-study
python scripts/empirical_study.py report studies/gpt-study
```

For a smoke test before committing API spend, use `--limit 2`.

## Interpretation rule

No statement that Evidence-First "improves," "reduces," or "outperforms" should be made until the completed study produces observed results. Report effect sizes, error rates, uncertainty, failures, model/provider, repository SHA, and study limitations together.
