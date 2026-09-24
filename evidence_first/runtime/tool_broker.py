from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evidence_first.tools.registry import ToolRegistry


SAFE_BUILTIN_TOOLS = frozenset(
    {
        "dataframe.profile",
        "dataframe.group_metric",
        "dataframe.correlation",
        "dataframe.before_after",
        "sql.query",
    }
)


@dataclass(frozen=True)
class ToolRequest:
    name: str
    arguments: dict[str, Any]
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolOutcome:
    name: str
    ok: bool
    value: Any = None
    error: str | None = None
    source_ids: tuple[str, ...] = ()


class ToolExecutionBroker:
    def __init__(
        self,
        registry: ToolRegistry,
        *,
        auto_allowed_tools: set[str] | frozenset[str] | None = None,
        trusted_source_ids: set[str] | frozenset[str] | None = None,
        max_batch_requests: int = 100,
    ):
        self.registry = registry
        self.auto_allowed_tools = frozenset(
            SAFE_BUILTIN_TOOLS if auto_allowed_tools is None else auto_allowed_tools
        )
        self.trusted_source_ids = frozenset(trusted_source_ids or ())
        self.max_batch_requests = max_batch_requests

    def execute(self, request: ToolRequest) -> ToolOutcome:
        try:
            spec = self.registry.get(request.name)
        except KeyError:
            return ToolOutcome(request.name, False, error="tool not registered")

        if request.name not in self.auto_allowed_tools:
            return ToolOutcome(
                request.name,
                False,
                error="automatic execution denied: tool is not operator-allowlisted",
            )
        if not spec.read_only:
            return ToolOutcome(
                request.name,
                False,
                error="automatic execution denied for non-read-only tool",
            )

        verified_sources = tuple(
            sid for sid in request.source_ids if sid in self.trusted_source_ids
        )
        try:
            value = spec.handler(**request.arguments)
            return ToolOutcome(
                request.name,
                True,
                value=value,
                source_ids=verified_sources,
            )
        except KeyboardInterrupt:
            raise
        except BaseException as exc:
            return ToolOutcome(
                request.name,
                False,
                error=f"{type(exc).__name__}: {exc}",
                source_ids=verified_sources,
            )

    def execute_many(self, requests: list[ToolRequest]) -> tuple[ToolOutcome, ...]:
        if len(requests) > self.max_batch_requests:
            return (
                ToolOutcome(
                    "__batch__",
                    False,
                    error=(
                        f"tool request batch exceeds limit "
                        f"{self.max_batch_requests}: {len(requests)}"
                    ),
                ),
            )
        return tuple(self.execute(request) for request in requests)
