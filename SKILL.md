---
name: evidence-first-root-cause
description: Investigate operational, business, healthcare, supply-chain, program, product, data-quality, and AI-system anomalies by validating the signal, testing competing hypotheses, seeking contradictory evidence, quantifying impact, and separating observation from inference before recommending action.
license: Apache-2.0
---

# Evidence-First Root Cause

## Purpose

Use this skill when an agent is asked why a measurable outcome changed, failed, deteriorated, or behaved unexpectedly.

The objective is not to produce the fastest explanation.

The objective is to produce the **best-supported explanation that survives attempts to disprove it**.

## Core Principle

Never ask only:

> What caused this?

Ask:

> What evidence would distinguish one plausible cause from another?

A plausible story is not evidence. Correlation is not automatically causation. A model-generated explanation is not evidence.

## Non-Negotiable Rules

1. Validate the signal before explaining it.
2. Separate measured observations from interpretation.
3. Generate multiple plausible hypotheses before selecting a leading explanation.
4. Seek evidence against the leading hypothesis.
5. Preserve meaningful uncertainty.
6. Never invent missing data.
7. Do not claim causation when the available design supports only association.
8. Quantify impact only where the data supports it.
9. Tie recommendations to the supported mechanism.
10. Define how the proposed intervention will be evaluated.
11. If the signal is unreliable, stop causal analysis.
12. If evidence cannot distinguish competing explanations, return `insufficient_evidence`.

## Workflow

### 1. Define the problem precisely

Capture the affected metric, expected baseline, observed value, magnitude, timing, affected population, comparison population, and operational consequence.

### 2. Validate the signal

Check, where relevant:

- data freshness
- missing records
- duplicates
- schema changes
- source-system changes
- pipeline failures
- instrumentation changes
- denominator changes
- metric-definition changes
- timezone/calendar changes
- seasonality
- sample-size instability
- delayed reporting
- one-time bulk loads
- filtering/join errors

If the signal cannot be trusted, return `data_quality_blocked`. Do not continue to business-cause inference.

### 3. Establish baseline and context

Use defensible comparisons such as prior periods, rolling averages, same period last year, target, unaffected control groups, or expected statistical ranges.

State why the baseline is appropriate.

### 4. Localize the anomaly

Segment by relevant dimensions such as time, geography, site, supplier, customer, product, payer, provider, process stage, shift, channel, device, model version, release, or data source.

Ask where the problem is concentrated, where it is absent, and when it began.

### 5. Generate competing hypotheses

For every hypothesis define:

- mechanism
- expected evidence
- disconfirming evidence
- required data

Include a measurement/data-quality hypothesis when appropriate.

### 6. Test hypotheses

Use methods appropriate to the question and available evidence, including descriptive comparison, contribution analysis, Pareto analysis, cohort analysis, variance decomposition, event sequences, time series, regression, controlled comparison, process mining, or qualitative process tracing.

State the limits of the method. Do not describe observational evidence as experimental evidence.

### 7. Seek contradictory evidence

Actively try to disprove the leading explanation.

Ask:

- If this were true, where else should the effect appear?
- Does it?
- Where should it not appear?
- Are there counterexamples?
- Did the suspected driver change before the outcome?
- Can a third variable explain both?
- Does the relationship survive segmentation?
- Does it survive an alternative baseline?

### 8. Quantify contribution and impact

Where supported, estimate affected volume, contribution share, financial exposure, operational impact, customer/patient impact, service-level impact, time loss, capacity loss, or risk exposure.

Do not report false precision.

### 9. Classify material findings

Use:

- `observation`: directly measured
- `inference`: interpretation supported by evidence but not directly observed
- `conclusion`: best-supported explanation after alternatives were tested
- `unknown`: unresolved due to insufficient evidence

### 10. Assign confidence

Use `high`, `medium`, or `low` based on data quality, temporal ordering, consistency across segments, alternative explanations, contradicting evidence, and causal-design strength.

State what would increase or reduce confidence.

### 11. Recommend action

Separate:

- containment
- corrective action
- preventive action
- additional investigation

Do not recommend irreversible intervention when evidence is weak.

### 12. Measure the intervention

Define the target metric, baseline, expected direction, review timing, comparison method, success threshold, and escalation/rollback criteria.

Root-cause analysis is incomplete until the intervention is measured.

## Required Machine-Readable Output

When structured output is requested, conform to:

`schemas/root_cause_output.schema.json`

Allowed statuses:

- `root_cause_supported`
- `multiple_contributors_supported`
- `insufficient_evidence`
- `data_quality_blocked`

Never force a root cause when evidence does not support one.

## Prohibited Behavior

Never:

- invent evidence
- use correlation alone as proof of causation
- hide contradictory evidence
- skip signal validation
- confuse symptoms with causes
- select a cause because it is narratively satisfying
- treat an LLM explanation as evidence
- silently change the baseline
- report unsupported precision
- suppress uncertainty
- recommend action unrelated to the supported mechanism
- declare success without a measurement plan

## Domain Extensions

Domain-specific skills may extend this method with specialized terminology, KPIs, validation rules, causal mechanisms, regulations, tools, or schemas.

They must preserve the evidence discipline defined here.
