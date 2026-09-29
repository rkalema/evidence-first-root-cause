from __future__ import annotations

import json
import os
import shlex
import subprocess
from collections.abc import Callable
from typing import Any

from .config import ProductConfig


JSONCall = Callable[[str], dict[str, Any]]


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        start = stripped.find("{")
        if start < 0:
            raise ValueError("provider returned no JSON object")
        try:
            parsed, end = decoder.raw_decode(stripped[start:])
        except json.JSONDecodeError as exc:
            raise ValueError(f"provider returned invalid JSON: {exc}") from exc
        trailing = stripped[start + end :].strip()
        if trailing and not trailing.startswith("```"):
            raise ValueError("provider returned text after the JSON object")

    if not isinstance(parsed, dict):
        raise ValueError("provider response JSON must be an object")
    return parsed


def _openai_call(config: ProductConfig) -> JSONCall:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "OpenAI provider requires the optional package: pip install openai"
        ) from exc

    client = OpenAI()

    def call(prompt: str) -> dict[str, Any]:
        response = client.responses.create(
            model=config.model,
            input=prompt,
        )
        text = getattr(response, "output_text", None)
        if not text:
            pieces: list[str] = []
            for item in getattr(response, "output", ()) or ():
                for block in getattr(item, "content", ()) or ():
                    value = getattr(block, "text", None)
                    if value:
                        pieces.append(value)
            text = "\n".join(pieces)
        if not text:
            raise RuntimeError("OpenAI provider returned no text output")
        return _parse_json_object(text)

    return call


def _anthropic_call(config: ProductConfig) -> JSONCall:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError(
            "Anthropic provider requires the optional package: pip install anthropic"
        ) from exc

    client = Anthropic()

    def call(prompt: str) -> dict[str, Any]:
        response = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        pieces = [
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text" and getattr(block, "text", None)
        ]
        if not pieces:
            raise RuntimeError("Anthropic provider returned no text output")
        return _parse_json_object("\n".join(pieces))

    return call


def _command_call(config: ProductConfig) -> JSONCall:
    argv = tuple(token.replace("{model}", config.model) for token in config.command)

    def call(prompt: str) -> dict[str, Any]:
        env = dict(os.environ)
        env["EFRC_MODEL"] = config.model
        try:
            completed = subprocess.run(
                argv,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=config.timeout_seconds,
                check=False,
                shell=False,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"provider command timed out after {config.timeout_seconds}s"
            ) from exc
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            raise RuntimeError(
                f"provider command failed with exit {completed.returncode}: "
                + (stderr[:1000] if stderr else "no stderr")
            )
        return _parse_json_object(completed.stdout)

    return call


def build_json_call(config: ProductConfig) -> JSONCall:
    if config.provider == "openai":
        return _openai_call(config)
    if config.provider == "anthropic":
        return _anthropic_call(config)
    if config.provider == "command":
        return _command_call(config)
    raise ValueError(f"unsupported provider: {config.provider}")


def provider_readiness(config: ProductConfig) -> dict[str, Any]:
    if config.provider == "openai":
        try:
            import openai  # noqa: F401
            package = True
        except ImportError:
            package = False
        return {
            "provider": "openai",
            "model": config.model,
            "package_installed": package,
            "credential_env": "OPENAI_API_KEY",
            "credential_present": bool(os.environ.get("OPENAI_API_KEY")),
            "ready": package and bool(os.environ.get("OPENAI_API_KEY")),
        }

    if config.provider == "anthropic":
        try:
            import anthropic  # noqa: F401
            package = True
        except ImportError:
            package = False
        return {
            "provider": "anthropic",
            "model": config.model,
            "package_installed": package,
            "credential_env": "ANTHROPIC_API_KEY",
            "credential_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "ready": package and bool(os.environ.get("ANTHROPIC_API_KEY")),
        }

    executable = config.command[0] if config.command else ""
    resolved = None
    if executable:
        import shutil

        resolved = shutil.which(executable)
    return {
        "provider": "command",
        "model": config.model,
        "command": list(config.command),
        "executable_found": bool(resolved),
        "ready": bool(resolved),
    }


def parse_command(value: str) -> tuple[str, ...]:
    argv = tuple(shlex.split(value))
    if not argv:
        raise ValueError("provider command cannot be empty")
    return argv
