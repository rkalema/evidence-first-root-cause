# Design

## What this project is

Evidence-First Root Cause is a reasoning-control layer for agents performing root-cause analysis.

It is designed to reduce these failure modes:

- premature causal stories
- correlation-as-causation
- ignored data-quality failures
- single-hypothesis anchoring
- suppression of contradictory evidence
- false precision
- overconfident recommendations
- interventions with no outcome measurement

## What this project is not

It is not:

- a causal-inference engine
- a replacement for domain expertise
- proof that an LLM conclusion is true
- a substitute for valid data collection
- a substitute for experimental design
- an autonomous authority for high-impact decisions

## Trust boundary

The skill governs analytical behavior, but it cannot independently verify that evidence supplied to the model is genuine.

Any production implementation should keep a traceable link between claims and source records.

## Evaluation philosophy

The benchmark suite does not reward verbosity.

It rewards specific behavior:

1. choosing the correct analysis status;
2. checking signal quality;
3. maintaining competing hypotheses;
4. exposing required contradictions;
5. avoiding forbidden conclusions;
6. calibrating confidence;
7. linking action to evidence;
8. defining an intervention test.

The scorer is deterministic so a benchmark result is reproducible.

## Why deterministic scoring

An LLM judge can be useful, but using an LLM as the only judge of another LLM can hide the same reasoning problems being tested.

The included scorer therefore checks explicit benchmark invariants.

Future external evaluations can add human or model judges, but deterministic checks remain the minimum gate.

## Failure-safe outcomes

Three outcomes are deliberately first-class:

- `data_quality_blocked`
- `insufficient_evidence`
- `multiple_contributors_supported`

The system must not be penalized for declining to make a causal claim when the evidence is weak.

## Benchmark integrity

Benchmark case files contain the facts, traps, and scoring requirements. Agents being tested should receive only the `prompt` and `facts`, not the `expected` section.

Do not expose gold expectations to the model under evaluation.

## High-impact use

Healthcare, finance, safety, employment, and other consequential domains require human review and domain-specific safeguards.

This repository provides analytical discipline, not authorization to automate consequential decisions.
