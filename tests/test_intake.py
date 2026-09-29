from evidence_first.intake import fingerprint_text, ingest_csv, ingest_json, ingest_text
from evidence_first.intake.evidence_adapter import to_evidence_payloads


def test_text_fingerprint_is_deterministic():
    assert fingerprint_text("abc") == fingerprint_text("abc")
    assert fingerprint_text("abc") != fingerprint_text("abcd")


def test_empty_text_is_blocking():
    result = ingest_text("   ", source_id="note")
    assert result.valid is False
    assert result.blocking_issues[0].code == "empty_source"


def test_json_object_becomes_one_record():
    result = ingest_json('{"metric":"sla","value":91}', source_id="incident.json")
    assert result.valid is True
    assert len(result.records) == 1
    assert result.records[0].payload["metric"] == "sla"


def test_invalid_json_is_blocking():
    result = ingest_json('{"metric":', source_id="bad.json")
    assert result.valid is False
    assert result.blocking_issues[0].code == "invalid_json"


def test_json_array_rejects_non_object_record():
    result = ingest_json('[{"x":1}, 2]', source_id="mixed.json")
    assert result.valid is False
    assert any(i.code == "non_object_record" for i in result.issues)


def test_csv_profiles_missingness_and_duplicates():
    text = "site,sla\nA,91\nB,\nA,91\n"
    result = ingest_csv(text, source_id="sla.csv")
    assert result.valid is True
    assert result.stats["record_count"] == 3
    assert result.stats["duplicate_row_count"] == 1
    assert result.stats["missing_cell_rate"] > 0
    assert {i.code for i in result.issues} >= {"duplicate_rows", "missing_values"}


def test_csv_duplicate_headers_block_ingestion():
    result = ingest_csv("site,site\nA,B\n", source_id="bad.csv")
    assert result.valid is False
    assert any(i.code == "duplicate_headers" for i in result.issues)


def test_evidence_adapter_preserves_provenance():
    result = ingest_csv("site,sla\nA,91\n", source_id="sla.csv")
    payload = to_evidence_payloads(result)[0]
    assert payload["source_id"] == "sla.csv"
    assert payload["source_fingerprint"].startswith("sha256:")
    assert payload["row_number"] == 2
