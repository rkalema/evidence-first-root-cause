from __future__ import annotations

import json
from io import StringIO

from evidence_first.product.demo import run_demo


def test_bundled_demo_completes_and_writes_auditable_workspace(tmp_path):
    stream = StringIO()
    artifacts = run_demo(out_dir=tmp_path, stream=stream)

    expected = {
        "run",
        "report",
        "evidence",
        "hypotheses",
        "audit",
        "result",
        "manifest",
    }
    assert expected <= set(artifacts)
    assert all(artifacts[name].exists() for name in expected)

    result = json.loads(artifacts["result"].read_text())
    assert result["stage"] == "complete"
    assert result["conclusion_gate"]["allowed"] is True

    audit = json.loads(artifacts["audit"].read_text())
    assert audit["events"]
    assert len(audit["events"]) == len(audit["audit_chain"])

    manifest = json.loads(artifacts["manifest"].read_text())
    assert manifest["provider"] == "demo"
    assert manifest["sources"][0]["fingerprint"].startswith("sha256:")

    output = stream.getvalue()
    assert "[1/13]" in output
    assert "[13/13]" in output
