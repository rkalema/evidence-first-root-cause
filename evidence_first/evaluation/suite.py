from __future__ import annotations
from dataclasses import dataclass
from .metrics import EvaluationAggregate,aggregate_scores

@dataclass(frozen=True)
class ComparisonSummary:
    baseline:EvaluationAggregate
    evidence_first:EvaluationAggregate
    mean_delta:float

def summarize_comparison(baseline_rows:list[dict],ef_rows:list[dict])->ComparisonSummary:
    if len(baseline_rows)!=len(ef_rows): raise ValueError("matched runs required")
    a=aggregate_scores(baseline_rows); b=aggregate_scores(ef_rows)
    return ComparisonSummary(a,b,round(b.mean_score-a.mean_score,2))
