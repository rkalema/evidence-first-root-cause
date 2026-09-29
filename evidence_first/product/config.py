from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


CONFIG_VERSION = 1
SUPPORTED_PROVIDERS = ("openai", "anthropic", "command")


@dataclass(frozen=True)
class ProductConfig:
    provider: str
    model: str
    runs_dir: str = "runs"
    command: tuple[str, ...] = ()
    timeout_seconds: int = 180
    max_tokens: int = 4096
    version: int = CONFIG_VERSION

    def __post_init__(self) -> None:
        if self.version != CONFIG_VERSION:
            raise ValueError(f"unsupported config version: {self.version}")
        if self.provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"unsupported provider {self.provider!r}; choose one of {SUPPORTED_PROVIDERS}"
            )
        if not self.model.strip():
            raise ValueError("model cannot be empty")
        if self.provider == "command" and not self.command:
            raise ValueError("command provider requires a command argv list")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")
        if self.max_tokens < 256:
            raise ValueError("max_tokens must be at least 256")

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ProductConfig":
        allowed = {
            "provider",
            "model",
            "runs_dir",
            "command",
            "timeout_seconds",
            "max_tokens",
            "version",
        }
        unknown = set(raw) - allowed
        if unknown:
            raise ValueError("unknown config field(s): " + ", ".join(sorted(unknown)))
        data = dict(raw)
        if "command" in data:
            command = data["command"]
            if isinstance(command, str):
                raise ValueError("command must be a JSON array of argv tokens, not a shell string")
            data["command"] = tuple(str(item) for item in command)
        return cls(**data)


def default_config_path() -> Path:
    override = os.environ.get("EFRC_CONFIG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".evidence-first" / "config.json"


def load_config(path: Path | None = None) -> ProductConfig | None:
    target = path or default_config_path()
    if not target.exists():
        return None
    raw = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Evidence-First config root must be a JSON object")
    return ProductConfig.from_dict(raw)


def save_config(config: ProductConfig, path: Path | None = None) -> Path:
    target = path or default_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    payload = asdict(config)
    payload["command"] = list(config.command)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    fd, temp_name = tempfile.mkstemp(
        prefix=target.name + ".",
        suffix=".tmp",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)

    return target
