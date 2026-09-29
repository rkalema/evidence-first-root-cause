from io import BytesIO
import pandas as pd
from evidence_first.intake.excel import ingest_xlsx_bytes

def test_excel_intake_preserves_rows_and_fingerprint():
    b=BytesIO()
    pd.DataFrame({"site":["A","B"],"sla":[91,None]}).to_excel(b,index=False)
    r=ingest_xlsx_bytes(b.getvalue(),source_id="sla.xlsx")
    assert r.valid is True
    assert r.stats["record_count"]==2
    assert r.source.fingerprint.startswith("sha256:")
    assert any(i.code=="missing_values" for i in r.issues)
