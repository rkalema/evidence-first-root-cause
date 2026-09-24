# Research Brief: Evidence-First

## Working title

**Evidence-Governed Investigation for Large Language Models: Reducing Unsupported Causal Conclusions in Business and Operational Analytics**

## Motivation

Large language models can synthesize complex information and generate plausible causal narratives. The same capability creates a reliability problem: a coherent explanation may be produced before the signal is validated, alternatives are tested, contradictory evidence is sought, or the underlying design can support a causal claim.

Evidence-First treats this as a systems-design problem rather than a prompt-writing problem.

## Proposed contribution

Evidence-First is a model-agnostic investigation architecture that separates evidence intake, signal validation, data-quality review, hypothesis generation, analytical testing, contradiction search, confound review, contribution estimation, independent critique, intervention planning, outcome evaluation, and investigation memory.

The architecture adds code-level governance around model reasoning:
- source fingerprints and provenance;
- explicit decision rights;
- causal stop states;
- read-only tool execution;
- conclusion gates;
- audit events;
- reproducible benchmark scoring;
- intervention falsification.

## Research questions

**RQ1.** Does Evidence-First reduce false causal conclusions relative to an unstructured LLM baseline?

**RQ2.** Does it improve detection of contradictory evidence and material confounding?

**RQ3.** Does it improve appropriate use of insufficient-evidence and data-quality-blocked outcomes?

**RQ4.** Does it improve traceability between conclusions and source evidence?

**RQ5.** Which components contribute most to performance improvement?

**RQ6.** What additional cost is introduced in tokens, elapsed time, and tool calls?

## Evaluation design

The initial laboratory contains 20 adversarial cases across business and operational domains. Baseline and Evidence-First conditions receive identical incidents, evidence, and output requirements. Gold expectations remain hidden. Runs use fresh contexts and matched model configurations.

Planned ablations remove signal validation, contradiction search, confound review, and the critic individually.

Synthetic benchmarking will be reported separately from real-data demonstrations. No claim of general causal-reasoning superiority will be made solely from synthetic cases.

## Intended significance

The project explores whether AI analytics can be made more reliable by governing the *process by which explanations earn authority*, rather than relying only on larger models or more detailed user prompts.
