# Example: Operations

## Scenario

A regional fulfillment SLA falls from 94% to 79%.

## Investigation pattern

Validate the metric, then segment by:

- facility
- shift
- carrier
- product class
- order size
- process stage
- day/hour

Generate competing hypotheses such as:

- demand exceeded capacity
- staffing shortage
- carrier pickup delay
- equipment downtime
- inventory-location mismatch
- data timestamp defect

Look for evidence that would distinguish them.

If carrier delay is the leading explanation, test whether arrival-time deterioration occurred before SLA deterioration and whether comparable unaffected sites using the same carrier show the same pattern.
