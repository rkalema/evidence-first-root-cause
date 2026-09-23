#!/usr/bin/env python3
"""CLI for Evidence-First."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from scripts.evaluate_case import score
from scripts.validate_output import validate_document
from evidence_first.intake import ingest_csv,ingest_json,ingest_text,ingest_xlsx_bytes
from evidence_first.domains import DOMAIN_PACKS
from evidence_first.evaluation.ablation import ablation_plan
from evidence_first.agents import AgentRole, InvestigationOrchestrator
from evidence_first.agents.artifacts import validate_artifact_flow

ROOT=Path(__file__).resolve().parent
CASES_DIR=ROOT/"benchmarks"/"cases"

def load_json(path:Path)->dict:
    with path.open("r",encoding="utf-8") as h:return json.load(h)

def cmd_validate(path:Path)->int:
    errors=validate_document(load_json(path))
    if errors:
        print("INVALID"); [print(f"- {e}") for e in errors]; return 1
    print("VALID"); return 0

def cmd_cases()->int:
    paths=sorted(CASES_DIR.glob("*.json"))
    for path in paths:
        case=load_json(path); print(f"{case['id']}: {case['title']}")
    print(f"TOTAL: {len(paths)}")
    return 0

def cmd_score(case_path:Path,result_path:Path)->int:
    result=load_json(result_path); errors=validate_document(result)
    if errors: print(json.dumps({"valid_schema":False,"errors":errors},indent=2)); return 1
    report=score(load_json(case_path),result); print(json.dumps(report,indent=2)); return 0 if report["passed"] else 1

def cmd_intake(path:Path)->int:
    ext=path.suffix.lower()
    if ext in {".xlsx",".xlsm"}:
        result=ingest_xlsx_bytes(path.read_bytes(),source_id=path.name)
    else:
        text=path.read_text(encoding="utf-8")
        result=ingest_csv(text,source_id=path.name) if ext==".csv" else ingest_json(text,source_id=path.name) if ext==".json" else ingest_text(text,source_id=path.name)
    print(json.dumps({"valid":result.valid,"source":result.source.__dict__,"stats":result.stats,"issues":[{"code":x.code,"message":x.message,"severity":x.severity.value} for x in result.issues]},indent=2))
    return 0 if result.valid else 1

def build_parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="efrc",description="Evidence-First investigation and evaluation toolkit.")
    sub=p.add_subparsers(dest="command",required=True)
    q=sub.add_parser("validate"); q.add_argument("result",type=Path)
    sub.add_parser("cases")
    q=sub.add_parser("score"); q.add_argument("case",type=Path); q.add_argument("result",type=Path)
    q=sub.add_parser("intake"); q.add_argument("source",type=Path)
    sub.add_parser("domains")
    sub.add_parser("ablations")\n    sub.add_parser("doctor")
    return p

def main()->int:
    a=build_parser().parse_args()
    if a.command=="validate":return cmd_validate(a.result)
    if a.command=="cases":return cmd_cases()
    if a.command=="score":return cmd_score(a.case,a.result)
    if a.command=="intake":return cmd_intake(a.source)
    if a.command=="domains": print("\n".join(sorted(DOMAIN_PACKS))); return 0
    if a.command=="ablations": print(json.dumps(ablation_plan(),indent=2)); return 0
    if a.command=="doctor":
        gaps=validate_artifact_flow(InvestigationOrchestrator().build_plan())
        checks={
            "agents":len(AgentRole),
            "artifact_flow_closed":not gaps,
            "benchmark_cases":len(list(CASES_DIR.glob("*.json"))),
            "domain_packs":len(DOMAIN_PACKS),
            "canonical_schema_exists":(ROOT/"schemas"/"root_cause_output.schema.json").exists(),
        }
        ok=checks["agents"]>=13 and checks["artifact_flow_closed"] and checks["benchmark_cases"]>=20 and checks["domain_packs"]>=6 and checks["canonical_schema_exists"]
        print(json.dumps({"status":"PASS" if ok else "FAIL","checks":checks,"artifact_gaps":[g.__dict__ for g in gaps]},indent=2))
        return 0 if ok else 1
    return 2
if __name__=="__main__": raise SystemExit(main())
