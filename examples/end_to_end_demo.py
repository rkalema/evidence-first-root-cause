from pathlib import Path
import pandas as pd
from evidence_first.intake import ingest_csv
from evidence_first.tools import DataFrameTool
from evidence_first.tools.provenance import analysis_to_evidence
from evidence_first.core.ledger import EvidenceLedger

path=Path(__file__).parent/'data'/'delivery_incident.csv'
text=path.read_text()
intake=ingest_csv(text,source_id=path.name)
assert intake.valid
frame=pd.read_csv(path)
tool=DataFrameTool(frame)
analysis=tool.group_metric('period','sla','mean')
evidence=analysis_to_evidence(analysis,source_ids=(intake.source.fingerprint,))
ledger=EvidenceLedger(); ledger.add_evidence(evidence)
print('source fingerprint:',intake.source.fingerprint)
print('profile:',tool.profile().value)
print('derived evidence:',ledger.evidence(evidence.evidence_id))
