# Evidence-First Empirical Validation Preregistration

Status: **frozen before live-model inference**

## Study question

Does the Evidence-First method reduce unsupported causal conclusions and improve evidence-governed investigation quality relative to a matched unstructured analytical baseline on the repository's adversarial benchmark corpus?

## Unit of analysis

One model generation for one benchmark case under one experimental condition.

A matched pair is the same case, model, provider, and repetition under:
- baseline
- Evidence-First

## Corpus

Twenty adversarial synthetic benchmark cases committed before live inference.

The benchmark manifest is verified before inference. Gold expectations are never included in prepared model prompts.

## Primary endpoint

**False causal conclusion rate on cases whose expected status is either**
- `insufficient_evidence`, or
- `data_quality_blocked`.

A false causal conclusion occurs when the model instead returns:
- `root_cause_supported`, or
- `multiple_contributors_supported`.

This endpoint is primary because the central system claim concerns preventing unsupported causal promotion.

## Secondary endpoints

1. Paired benchmark score delta.
2. Pass rate.
3. Correct `insufficient_evidence` rate.
4. Correct `data_quality_blocked` rate.
5. Schema-valid output rate.
6. Contradiction/concept detection captured by the deterministic scorer.
7. Input tokens.
8. Output tokens.
9. Wall-clock latency.

## Hypotheses

### H1 — primary
Evidence-First will have a lower false causal conclusion rate than baseline on non-causal-stop benchmark cases.

### H2
Evidence-First will have a positive mean paired benchmark-score delta relative to baseline.

### H3
Evidence-First will improve correct `insufficient_evidence` and `data_quality_blocked` decisions.

### H4
Evidence-First will use more tokens and/or latency than baseline because it imposes additional reasoning structure.

H4 is a cost hypothesis, not a quality failure.

## Design

- matched within-case design
- same provider/model for both conditions
- three repetitions per condition per case by default
- 20 cases × 2 conditions × 3 repetitions = 120 planned generations
- fresh context for every generation
- deterministic randomized execution order
- same user evidence and same output contract
- only system-method instructions differ
- temperature and other provider controls held constant when the provider exposes them

## Randomization

The study harness uses a recorded pseudorandom seed. Default seed:

`20260928`

Trial order is written into the study manifest before inference.

## Blinding and leakage controls

During inference, the model receives:
- case evidence
- case ID
- requested output contract
- condition-specific system instructions

It does not receive:
- `expected`
- pass thresholds
- forbidden-term lists
- scorer implementation
- benchmark trap catalog
- gold status

Prompt files are SHA-256 hashed before execution and verified before scoring.

## Exclusions

No completed model generation is excluded because it performs poorly.

A trial may be classified as technically failed if:
- provider request fails,
- timeout occurs,
- no parseable JSON object is returned,
- output cannot be associated with its trial.

Technical failures remain in the study record and are reported by condition.

Malformed/schema-invalid model output receives the deterministic scoring consequence defined before inference; it is not manually repaired.

## Re-runs

A failed API request may be retried only under a documented mechanical retry policy. A semantically poor but technically valid answer is never re-run merely to improve the result.

## Statistical analysis

### Primary endpoint
Report false causal conclusion rate separately for baseline and Evidence-First, with raw numerators and denominators.

### Paired score endpoint
For paired score deltas:
- mean delta
- median delta
- wins / ties / losses
- exact two-sided sign test
- deterministic bootstrap 95% confidence interval for mean paired delta

The sign test is included because score differences need not be normally distributed.

## Multiplicity

Only H1 is treated as the primary confirmatory hypothesis. Other endpoints are secondary/descriptive. No claim of broad scientific proof is based solely on nominal significance from secondary outcomes.

## Ablations

Ablations are run only after the baseline-vs-full study is frozen:

- no signal validation
- no contradiction search
- no confound review
- no critic

Ablation analyses are secondary and reported as component-sensitivity analyses.

Prompt-only ablations and runtime-stage ablations must be labeled separately.

## Reporting commitments

The final report will include:
- provider/model
- repository SHA
- benchmark manifest
- study seed
- repetitions
- all planned and failed trials
- raw condition counts
- primary and secondary outcomes
- latency/token cost
- ablations
- limitations
- synthetic-vs-real-data distinction

No result will be described as proving causal reasoning ability or general real-world superiority.

## Freeze rule

After the first live trial is executed, changes to this preregistration must be appended as dated amendments rather than silently editing the original analysis plan.
