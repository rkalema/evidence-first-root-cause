# Research Protocol

## Core question
Does evidence-governed investigation reduce unsupported causal conclusions and improve traceability, contradiction detection, uncertainty calibration, and falsification behavior relative to an unstructured LLM baseline?

## Primary outcomes
- false causal conclusion rate
- correct insufficient-evidence rate
- correct data-quality-stop rate
- contradiction detection rate
- confound detection rate
- evidence traceability score
- intervention falsifiability score
- total tokens, elapsed time, and tool calls

## Design
Each case is evaluated under matched evidence and matched output requirements. Gold expectations are hidden from the model. Baseline and Evidence-First runs use fresh contexts. Model and temperature are held constant where supported.

## Ablations
Run the complete system, then remove signal validation, contradiction search, confound review, and critic stages one at a time. Report whether each component materially changes failure rates.

## Reporting
Report observed results only. Do not infer scientific generality from synthetic cases. Separate synthetic benchmarks, real-data demonstrations, and any human-rated study.
