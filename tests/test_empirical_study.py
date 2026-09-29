from __future__ import annotations

import json
from pathlib import Path

from evidence_first.evaluation.study import (
    load_manifest,
    prepare_study,
    score_completed_study,
    summarize_study,
    verify_manifest,
)


def test_prepare_study_is_blind_balanced_and_reproducible(tmp_path):
    manifest_path = prepare_study(
        tmp_path,
        provider="command",
        model="test-model",
        repository_sha="abc123",
        repetitions=2,
        seed=7,
    )
    manifest = load_manifest(manifest_path)
    verify_manifest(tmp_path, manifest)

    assert len(manifest["trials"]) == 20 * 2 * 2
    counts = {}
    for trial in manifest["trials"]:
        counts[trial["condition"]] = counts.get(trial["condition"], 0) + 1
        text = (tmp_path / trial["prompt_path"]).read_text()
        assert '"expected"' not in text
        assert '"pass_score"' not in text
    assert counts == {"baseline": 40, "evidence-first": 40}

    second = tmp_path / "second"
    second_manifest = load_manifest(
        prepare_study(
            second,
            provider="command",
            model="test-model",
            repository_sha="abc123",
            repetitions=2,
            seed=7,
        )
    )
    order1 = [x["trial_id"] for x in manifest["trials"]]
    order2 = [x["trial_id"] for x in second_manifest["trials"]]
    assert order1 == order2


def test_manifest_detects_prompt_tampering(tmp_path):
    manifest_path = prepare_study(
        tmp_path,
        provider="command",
        model="m",
        repository_sha="sha",
        repetitions=1,
        seed=1,
    )
    manifest = load_manifest(manifest_path)
    prompt = tmp_path / manifest["trials"][0]["prompt_path"]
    prompt.write_text(prompt.read_text() + "\nTAMPER")
    try:
        verify_manifest(tmp_path, manifest)
        raise AssertionError("prompt tampering was not detected")
    except ValueError as exc:
        assert "hash mismatch" in str(exc)


def test_paired_summary_reports_delta_and_false_causal_rate():
    rows = [
        {
            "case_id": "a",
            "condition": "baseline",
            "repetition": 1,
            "score": 50,
            "passed": False,
            "valid_schema": True,
            "expected_status": "insufficient_evidence",
            "actual_status": "root_cause_supported",
            "elapsed_seconds": 1.0,
            "input_tokens": 10,
            "output_tokens": 20,
        },
        {
            "case_id": "a",
            "condition": "evidence-first",
            "repetition": 1,
            "score": 90,
            "passed": True,
            "valid_schema": True,
            "expected_status": "insufficient_evidence",
            "actual_status": "insufficient_evidence",
            "elapsed_seconds": 2.0,
            "input_tokens": 15,
            "output_tokens": 25,
        },
    ]
    summary = summarize_study(rows, seed=1)
    assert summary["paired"]["mean_score_delta"] == 40
    assert summary["paired"]["wins"] == 1
    assert summary["false_causal_rate"]["baseline"] == 1.0
    assert summary["false_causal_rate"]["evidence-first"] == 0.0
