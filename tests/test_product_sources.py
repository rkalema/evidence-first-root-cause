from __future__ import annotations

import hashlib

from evidence_first.product.sources import prepare_sources


def test_prepare_sources_preserves_file_fingerprint_and_no_absolute_path(tmp_path):
    path = tmp_path / "ops.csv"
    raw = b"site,sla\nA,91\nB,85\n"
    path.write_bytes(raw)

    prepared = prepare_sources([path])
    item = prepared.source_inventory[0]

    assert item["fingerprint"] == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert "path" not in item
    assert item["source_id"] == "ops.csv"
    assert prepared.tool_broker is not None
    assert any(record.source == "ops.csv" for record in prepared.evidence_records)


def test_prepare_sources_rejects_blocking_intake_defect(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("a,a\n1,2\n")

    try:
        prepare_sources([path])
        assert False, "invalid source should not enter an investigation"
    except ValueError as exc:
        assert "blocking intake" in str(exc)


def test_prepare_sources_rejects_duplicate_source_ids(tmp_path):
    one = tmp_path / "one"
    two = tmp_path / "two"
    one.mkdir()
    two.mkdir()
    (one / "same.csv").write_text("x\n1\n")
    (two / "same.csv").write_text("x\n2\n")

    try:
        prepare_sources([one / "same.csv", two / "same.csv"])
        assert False
    except ValueError as exc:
        assert "source IDs must be unique" in str(exc)
