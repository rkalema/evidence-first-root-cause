from __future__ import annotations
import hashlib,json
from evidence_first.core.models import EvidenceKind,EvidenceRecord
from .dataframe import AnalysisResult

def analysis_to_evidence(result:AnalysisResult,*,source_ids:tuple[str,...],tool_name:str='dataframe')->EvidenceRecord:
    payload={'operation':result.operation,'value':result.value,'metadata':result.metadata,'source_ids':source_ids,'tool':tool_name}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()[:16]
    return EvidenceRecord('derived-'+digest,json.dumps(result.value,sort_keys=True,default=str),EvidenceKind.TOOL_OUTPUT,tool_name,metadata={'source_ids':source_ids,'operation':result.operation,'analysis_metadata':result.metadata})
