from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class DomainPack:
    name:str
    key_metrics:tuple[str,...]
    common_confounders:tuple[str,...]
    validation_checks:tuple[str,...]
    caution:str

DOMAIN_PACKS={
"operations":DomainPack("operations",("throughput","cycle_time","sla","capacity","defects"),("demand mix","staffing","shift","site","seasonality"),("process-stage timestamps","control sites","denominator integrity"),"Distinguish bottleneck location from downstream symptoms."),
"supply_chain":DomainPack("supply_chain",("fill_rate","otif","lead_time","inventory_turns","stockouts"),("demand spike","supplier mix","transport disruption","allocation policy"),("sku/site segmentation","order completeness","inventory snapshots"),"Avoid attributing stockouts solely to supplier performance without allocation and demand evidence."),
"customer_analytics":DomainPack("customer_analytics",("retention","conversion","churn","cac","ltv"),("channel mix","cohort age","selection","campaign targeting"),("within-cohort stability","attribution quality","denominator consistency"),"Aggregate movement may be compositional."),
"healthcare_operations":DomainPack("healthcare_operations",("wait_time","los","readmission","mortality","denials"),("case mix","acuity","coding","denominator feeds"),("patient-count reconciliation","case-mix segmentation","source completeness"),"High-impact conclusions require domain review."),
"ai_data_incidents":DomainPack("ai_data_incidents",("accuracy","latency","error_rate","drift","coverage"),("traffic mix","model version","feature pipeline","label delay"),("version segmentation","data freshness","rollback comparison"),"Do not treat model correlation as proof of failure mechanism."),
"program_performance":DomainPack("program_performance",("delivery_rate","milestone_variance","benefit_realization","cost_variance"),("scope change","dependency delays","resource shifts"),("baseline versioning","dependency tracing","milestone timestamps"),"Separate delivery symptoms from upstream dependency causes.")
}

def get_domain_pack(name:str)->DomainPack:
    if name not in DOMAIN_PACKS: raise KeyError(name)
    return DOMAIN_PACKS[name]
