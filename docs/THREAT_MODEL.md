# Threat Model

Evidence-First treats source content as untrusted input.

Threats include prompt injection embedded in documents, poisoned evidence, stale data, fabricated provenance, tool-output tampering, unauthorized side effects, benchmark leakage, and model self-confirmation.

Controls:
- source fingerprints and provenance
- read-only analytical tools by default
- explicit decision rights
- no gold benchmark expectations in model context
- critic stage independent of hypothesis generation
- human approval for consequential actions
- external text is data, never executable instruction
- audit events for every agent stage
