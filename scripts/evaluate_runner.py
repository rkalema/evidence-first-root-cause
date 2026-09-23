#!/usr/bin/env python3
"""Controlled baseline-vs-Evidence-First evaluation runner."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from scripts.evaluate_case import score
from scripts.validate_output import validate_document

ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/"benchmarks"/"cases"

BASELINE_SYSTEM="You are an analytical assistant. Use only supplied evidence. Do not invent facts."
EF_SYSTEM="Use the Evidence-First Root Cause method exactly. Preserve uncertainty, test alternatives, seek contradictions, and do not invent evidence."

def load_case(case_id:str)->dict:
    return json.loads((CASES/f"{case_id}.json").read_text())

def user_prompt(case:dict)->str:
    facts="\n".join(f"- {x}" for x in case["facts"])
    return f'{case["prompt"]}\n\nEVIDENCE\n{facts}\n\nReturn the canonical Evidence-First JSON output contract.'

def prompt_packet(case_id:str,mode:str)->dict:
    case=load_case(case_id)
    if mode not in {"baseline","evidence-first"}: raise ValueError(mode)
    return {"case_id":case_id,"mode":mode,"system":BASELINE_SYSTEM if mode=="baseline" else EF_SYSTEM,"user":user_prompt(case)}

def prepare(case_id:str,out:Path)->tuple[Path,Path]:
    out.mkdir(parents=True,exist_ok=True)
    a=out/f"{case_id}.baseline.prompt.json"; b=out/f"{case_id}.evidence-first.prompt.json"
    a.write_text(json.dumps(prompt_packet(case_id,"baseline"),indent=2))
    b.write_text(json.dumps(prompt_packet(case_id,"evidence-first"),indent=2))
    return a,b

def score_result(case_id:str,result_path:Path)->dict:
    result=json.loads(result_path.read_text())
    errors=validate_document(result)
    if errors: return {"valid_schema":False,"errors":errors,"passed":False,"score":0}
    return {"valid_schema":True,**score(load_case(case_id),result)}

def compare(case_id:str,baseline:Path,evidence_first:Path)->dict:
    a=score_result(case_id,baseline); b=score_result(case_id,evidence_first)
    return {"case_id":case_id,"baseline":a,"evidence_first":b,"delta":round(float(b.get("score",0))-float(a.get("score",0)),1)}

def suite(manifest_path:Path)->dict:
    manifest=json.loads(manifest_path.read_text())
    rows=[]
    for item in manifest:
        rows.append(compare(item["case_id"],Path(item["baseline"]),Path(item["evidence_first"])))
    baseline_scores=[float(x["baseline"].get("score",0)) for x in rows]
    ef_scores=[float(x["evidence_first"].get("score",0)) for x in rows]
    n=len(rows)
    return {
        "n":n,
        "baseline_mean":round(sum(baseline_scores)/n,2) if n else 0,
        "evidence_first_mean":round(sum(ef_scores)/n,2) if n else 0,
        "mean_delta":round((sum(ef_scores)-sum(baseline_scores))/n,2) if n else 0,
        "cases":rows,
    }

def main()->int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    q=sub.add_parser("prepare"); q.add_argument("case_id"); q.add_argument("--out",type=Path,default=Path("runs"))
    q=sub.add_parser("score"); q.add_argument("case_id"); q.add_argument("result",type=Path)
    q=sub.add_parser("compare"); q.add_argument("case_id"); q.add_argument("baseline",type=Path); q.add_argument("evidence_first",type=Path)\n    q=sub.add_parser("suite"); q.add_argument("manifest",type=Path)
    a=p.parse_args()
    if a.cmd=="prepare":
        print("\n".join(map(str,prepare(a.case_id,a.out)))); return 0
    if a.cmd=="score":
        r=score_result(a.case_id,a.result); print(json.dumps(r,indent=2)); return 0 if r.get("passed") else 1
    if a.cmd=="compare":\n        r=compare(a.case_id,a.baseline,a.evidence_first); print(json.dumps(r,indent=2)); return 0\n    r=suite(a.manifest); print(json.dumps(r,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
