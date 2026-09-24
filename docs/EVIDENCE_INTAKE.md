# Evidence Intake

Evidence Intake is the boundary between external source material and the governed investigation system.

## Responsibilities

- fingerprint every source using SHA-256;
- preserve source identifiers and row provenance;
- parse CSV, JSON, and plain text;
- detect blocking parse/schema problems;
- surface missing values and duplicate rows as explicit quality issues;
- preserve raw records for later evidence normalization;
- never convert source rows directly into causal conclusions.

## Trust rule

Successful parsing means only that the source can be read. It does **not** mean the data is correct, complete, representative, fresh, or causally informative.

The Data Quality Investigator and Signal Validator remain responsible for those decisions.

## Initial stop conditions

The intake layer marks a source invalid when it encounters conditions such as:

- malformed JSON;
- unsupported JSON root types;
- non-object records in a JSON array;
- missing CSV headers;
- blank or duplicate CSV headers;
- empty text sources;
- CSV files with no data rows.

Missing cell values and duplicate data rows are warnings because whether they are fatal depends on the investigation context.
