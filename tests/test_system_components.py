import pandas as pd
from evidence_first.tools.dataframe import DataFrameTool
from evidence_first.tools.registry import ToolRegistry,ToolSpec
from evidence_first.memory import InvestigationMemory,MemoryEntry
from evidence_first.domains import get_domain_pack
from evidence_first.evaluation import aggregate_scores,ablation_plan

def test_dataframe_profile_and_grouping():
    df=pd.DataFrame({"g":["a","a","b"],"x":[1,3,10]})
    t=DataFrameTool(df)
    assert t.profile().value["rows"]==3
    assert t.group_metric("g","x").value["a"]==2.0

def test_tool_registry_rejects_duplicates():
    r=ToolRegistry(); spec=ToolSpec("x","demo",True,lambda:1); r.register(spec)
    try: r.register(spec); assert False
    except ValueError: pass

def test_memory_is_not_evidence_store():
    m=InvestigationMemory()
    m.add(MemoryEntry("i1","pricing caused decline","disproved",("e1",)))
    assert m.search("pricing")[0].outcome=="disproved"

def test_domain_pack_has_controls():
    p=get_domain_pack("customer_analytics")
    assert "channel mix" in p.common_confounders

def test_evaluation_metrics():
    a=aggregate_scores([{"score":80,"passed":False,"false_causal_conclusion":True},{"score":100,"passed":True,"false_causal_conclusion":False}])
    assert a.mean_score==90
    assert a.pass_rate==0.5
    assert a.false_causal_rate==0.5

def test_ablation_contains_full_system():
    assert ablation_plan()[0]["name"]=="full_system"
