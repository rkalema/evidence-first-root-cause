from __future__ import annotations
from io import BytesIO
from typing import Any
import pandas as pd
from .fingerprint import fingerprint_bytes
from .models import IntakeIssue,IntakeRecord,IntakeResult,IssueSeverity,SourceDescriptor

def ingest_xlsx_bytes(data:bytes,*,source_id:str,sheet_name:str|int=0,metadata:dict[str,Any]|None=None)->IntakeResult:
    source=SourceDescriptor(source_id,"xlsx",fingerprint_bytes(data),len(data),metadata or {})
    issues:list[IntakeIssue]=[]
    try:
        frame=pd.read_excel(BytesIO(data),sheet_name=sheet_name)
    except Exception as exc:
        issues.append(IntakeIssue("invalid_xlsx",f"Excel parse error: {type(exc).__name__}.",IssueSeverity.ERROR))
        return IntakeResult(source,(),tuple(issues),False,{"record_count":0})
    if len(frame.columns)==0:
        issues.append(IntakeIssue("missing_header","Worksheet has no columns.",IssueSeverity.ERROR))
    duplicate_headers=[str(c) for c in frame.columns[frame.columns.duplicated()].tolist()]
    if duplicate_headers:
        issues.append(IntakeIssue("duplicate_headers","Worksheet contains duplicate headers: "+", ".join(duplicate_headers),IssueSeverity.ERROR))
    duplicate_rows=int(frame.duplicated().sum())
    missing=int(frame.isna().sum().sum()); total=int(frame.shape[0]*frame.shape[1])
    if duplicate_rows:
        issues.append(IntakeIssue("duplicate_rows",f"Detected {duplicate_rows} duplicate row(s).",IssueSeverity.WARNING))
    if missing:
        issues.append(IntakeIssue("missing_values",f"Blank-cell rate is {missing/total:.1%}.",IssueSeverity.WARNING))
    records=[]
    for idx,row in frame.iterrows():
        payload={str(k):(None if pd.isna(v) else v.item() if hasattr(v,"item") else v) for k,v in row.to_dict().items()}
        records.append(IntakeRecord(f"r{len(records)+1}",source_id,payload,int(idx)+2))
    if not records:
        issues.append(IntakeIssue("no_data_rows","Worksheet contains headers but no data rows.",IssueSeverity.ERROR))
    valid=not any(i.severity is IssueSeverity.ERROR for i in issues)
    stats={"record_count":len(records),"column_count":len(frame.columns),"missing_cell_rate":round(missing/total,6) if total else 0.0,"duplicate_row_count":duplicate_rows,"headers":[str(c) for c in frame.columns]}
    return IntakeResult(source,tuple(records),tuple(issues),valid,stats)
