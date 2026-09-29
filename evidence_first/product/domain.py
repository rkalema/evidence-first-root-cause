from __future__ import annotations

from evidence_first.domains import DOMAIN_PACKS


KEYWORDS = {
    "operations": (
        "sla",
        "throughput",
        "cycle time",
        "capacity",
        "warehouse",
        "depot",
        "dispatch",
        "staffing",
    ),
    "supply_chain": (
        "supplier",
        "inventory",
        "stockout",
        "lead time",
        "otif",
        "fill rate",
        "shipment",
        "port",
    ),
    "customer_analytics": (
        "retention",
        "conversion",
        "churn",
        "customer",
        "campaign",
        "acquisition",
        "marketing",
    ),
    "healthcare_operations": (
        "patient",
        "hospital",
        "readmission",
        "mortality",
        "claims",
        "denial",
        "clinical",
    ),
    "ai_data_incidents": (
        "model",
        "latency",
        "drift",
        "prediction",
        "ai",
        "feature",
        "label",
        "pipeline",
    ),
    "program_performance": (
        "program",
        "project",
        "milestone",
        "dependency",
        "schedule",
        "benefit",
        "scope",
    ),
}


def detect_domain(question: str) -> str:
    text = question.lower()
    scored = {
        domain: sum(1 for keyword in keywords if keyword in text)
        for domain, keywords in KEYWORDS.items()
    }
    best = max(scored, key=scored.get)
    if scored[best] == 0:
        return "operations"
    return best


def validate_domain(domain: str) -> str:
    if domain not in DOMAIN_PACKS:
        raise ValueError(
            f"unknown domain {domain!r}; choose one of {sorted(DOMAIN_PACKS)}"
        )
    return domain
