---
name: evidence-first-root-cause
description: Investigate operational, business, healthcare, supply-chain, program, product, data-quality, and AI-system anomalies by validating the signal, testing competing hypotheses, seeking contradictory evidence, quantifying impact, and separating observation from inference before recommending action.
version: 0.1.0
license: Apache-2.0
---

# Evidence-First Root Cause

## Purpose

Use this skill when a user or system asks:

- Why did a KPI change?
- What caused an operational failure?
- Why did performance deteriorate?
- What is driving an anomaly?
- Why did a process, program, supplier, site, product, model, or workflow underperform?
- Which explanation is best supported by the available evidence?
- What should be investigated or changed next?

The objective is not to produce the fastest explanation.

The objective is to produce the **best-supported explanation that survives attempts to disprove it**.

## Core Principle

Never ask only:

> What caused this?

Ask:

> What evidence would distinguish one plausible cause from another?

A plausible story is not evidence.

A correlation is not automatically a cause.

A model-generated explanation is not automatically evidence.

## Non-Negotiable Rules

1. Validate the signal before explaining it.
2. Separate measured observations from interpretation.
3. Generate multiple plausible hypotheses before selecting a leading explanation.
4. Look for evidence against the leading hypothesis.
5. Preserve meaningful uncertainty.
6. Do not invent missing data.
7. Do not claim causation when the available design supports only association.
8. Quantify impact where the data supports it.
9. Tie recommendations to the supported mechanism.
10. Define how the proposed intervention will be evaluated.

If the data cannot support a root-cause conclusion, say so and identify the next evidence required.

# Workflow

## Stage 1: Define the Problem Precisely

Capture:

- metric or outcome affected
- expected baseline
- observed value
- absolute and percentage deviation
- start time
- duration
- affected population
- comparison population
- operational/business consequence

Avoid vague problem definitions such as:

- "performance is down"
- "customers are unhappy"
- "the supplier is failing"
- "the model got worse"

Convert the problem into a measurable statement.

## Stage 2: Validate the Signal

Before causal analysis, determine whether the anomaly is real.

Check, where relevant:

- data freshness
- missing records
- duplicate records
- schema changes
- source-system changes
- ETL/pipeline failures
- instrumentation changes
- denominator changes
- metric-definition changes
- timezone/calendar changes
- seasonality
- sample-size instability
- delayed reporting
- one-time bulk loads
- filtering/join errors

### Stop Condition

If the signal cannot be trusted:

1. classify the result as `data_quality_blocked`,
2. explain why,
3. identify the minimum repair/evidence needed,
4. stop causal inference until the signal is reliable.

Do not invent a business cause for a data-quality problem.

## Stage 3: Establish Baseline and Context

Choose defensible comparisons.

Possible baselines include:

- prior periods
- rolling averages
- same period last year
- operational target
- unaffected control group
- comparable site/product/provider/supplier
- expected statistical range

State why the selected baseline is appropriate.

Do not choose a comparison window merely because it strengthens a preferred story.

## Stage 4: Localize the Anomaly

Segment the outcome across dimensions relevant to the domain.

Examples:

- time
- geography
- site
- supplier
- customer segment
- product
- payer
- provider
- procedure
- shift
- employee group
- process stage
- channel
- device
- model version
- software release
- data source

Ask:

- Where is the problem concentrated?
- Where is it absent?
- When did it begin?
- Which groups changed most?
- Which groups did not change?

## Stage 5: Generate Competing Hypotheses

Produce multiple plausible explanations.

For every hypothesis define:

- `hypothesis`
- `mechanism`
- `expected_evidence`
- `disconfirming_evidence`
- `required_data`

Do not allow the first plausible explanation to become the conclusion.

Include a measurement/data-quality hypothesis when appropriate.

## Stage 6: Test the Hypotheses

Use methods appropriate to the question and available data.

Examples include:

- descriptive comparison
- contribution analysis
- Pareto analysis
- funnel decomposition
- cohort analysis
- variance decomposition
- event-sequence analysis
- time-series analysis
- control charts
- regression
- matched comparison
- interrupted time-series analysis
- controlled experiment
- process mining
- event-log analysis
- qualitative process tracing

For each method state important limitations.

Do not describe an observational comparison as an experiment.

Do not claim causal identification unless the design supports it.

## Stage 7: Seek Contradictory Evidence

Actively try to disprove the current leading explanation.

Ask:

- If this hypothesis were true, where else should the effect appear?
- Does it?
- Where should the effect not appear?
- Are there counterexamples?
- Did the suspected driver change before the outcome?
- Did the outcome change before the suspected driver?
- Is there a third variable that could explain both?
- Does the relationship survive segmentation?
- Does the relationship survive an alternative baseline?

## Stage 8: Quantify Contribution and Impact

Where the evidence permits, estimate:

- affected volume
- share of deterioration attributable to the driver
- financial exposure
- operational impact
- customer/patient impact
- service-level effect
- time lost
- capacity lost
- risk exposure

Do not report false precision.

## Stage 9: Classify Every Material Finding

Use these evidence classes.

### Observation
Directly supported by measured evidence.

### Inference
A reasonable interpretation of measured evidence that is not directly observed.

### Conclusion
The best-supported explanation after competing hypotheses were evaluated.

### Unknown
An unresolved question with insufficient evidence.

## Stage 10: Assign Confidence

Use:

- `high`
- `medium`
- `low`

Confidence must be based on evidence quality.

Consider:

- data reliability
- temporal ordering
- consistency across segments
- strength of alternative explanations
- number and quality of tests
- contradictory evidence
- causal design strength

State what evidence would increase or reduce confidence.

## Stage 11: Recommend Action

Separate recommendations into:

### Containment
Immediate steps to limit damage while investigation or repair continues.

### Corrective Action
Action aimed at the best-supported mechanism.

### Preventive Action
Changes that reduce recurrence risk.

### Additional Investigation
Evidence needed before stronger intervention.

Do not recommend an expensive or irreversible intervention when the evidence is weak.

## Stage 12: Define the Intervention Measurement Plan

Before action, define:

- target metric
- current baseline
- expected direction
- expected magnitude if defensible
- review date
- comparison method
- success threshold
- rollback/escalation criteria

A root-cause process is incomplete if nobody checks whether the intervention changed the outcome.

# Required Output

When machine-readable output is requested, produce JSON conforming to:

`schemas/root_cause_output.schema.json`

When narrative output is requested, use this structure:

## Problem
## Signal Validation
## Key Observations
## Hypotheses Tested
## Leading Explanation
## Confidence
## Impact
## Unknowns
## Recommended Actions
## Validation Plan

# Status Values

Use one of:

- `root_cause_supported`
- `multiple_contributors_supported`
- `insufficient_evidence`
- `data_quality_blocked`

Do not force a root cause when the appropriate status is `insufficient_evidence`.

# Anti-Patterns

Never:

- invent evidence
- use correlation alone as proof of causation
- hide contradictory evidence
- skip data-quality validation
- confuse a symptom with a cause
- select a cause because it is narratively satisfying
- use an LLM explanation as evidence
- silently change the baseline
- report unsupported precision
- suppress uncertainty
- recommend action unrelated to the supported mechanism
- declare success without a measurement plan

# Domain Adaptation

This skill is intentionally domain-neutral.

Domain-specific skills may extend it with specialized terminology, validation rules, KPIs, causal mechanisms, regulations, tools, and schemas.

Examples include healthcare claims, supply chain, workforce operations, program performance, manufacturing, customer retention, incident response, and model/agent reliability.

Domain extensions must preserve the evidence discipline defined here.
