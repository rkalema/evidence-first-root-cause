from __future__ import annotations

import json
import sys

from evidence_first.product.config import ProductConfig, load_config, save_config
from evidence_first.product.providers import build_json_call, provider_readiness


def test_config_roundtrip_does_not_store_api_keys(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setenv("OPENAI_API_KEY", "secret-test-value")

    config = ProductConfig(provider="openai", model="example-model")
    save_config(config, path)

    text = path.read_text()
    assert "secret-test-value" not in text
    assert "api_key" not in text.lower()
    assert load_config(path) == config


def test_unknown_secret_field_is_rejected():
    try:
        ProductConfig.from_dict(
            {
                "provider": "openai",
                "model": "x",
                "api_key": "should-not-be-stored",
            }
        )
        assert False, "secret-bearing unknown config field should be rejected"
    except ValueError:
        pass


def test_command_provider_uses_argv_and_json_stdout(tmp_path):
    script = tmp_path / "provider.py"
    script.write_text(
        "import json,sys\n"
        "prompt=sys.stdin.read()\n"
        "print(json.dumps({'decision':'block','summary':'seen',"
        "'artifacts':{},'evidence_ids':[],'unknowns':[],"
        "'next_requests':[str(len(prompt))]}))\n"
    )
    config = ProductConfig(
        provider="command",
        model="local-test",
        command=(sys.executable, str(script)),
    )
    readiness = provider_readiness(config)
    assert readiness["ready"]

    raw = build_json_call(config)("hello")
    assert raw["summary"] == "seen"
    assert raw["next_requests"] == ["5"]


def test_command_provider_rejects_shell_string():
    try:
        ProductConfig.from_dict(
            {
                "provider": "command",
                "model": "x",
                "command": "python provider.py; rm -rf /",
            }
        )
        assert False
    except ValueError:
        pass
