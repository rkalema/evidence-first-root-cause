from __future__ import annotations

from evidence_first.runtime.engine import InvestigationRun


def _safe_text(value: str) -> str:
    # Agent-controlled text cannot create Markdown headings or HTML blocks.
    return (
        value.replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_investigation_report(run: InvestigationRun) -> str:
    lines = [
        "# Evidence-First Investigation Report",
        "",
        f"**Question:** {_safe_text(run.question)}",
        f"**Stage:** {run.stage.value}",
        "",
    ]
    if run.blocked_by:
        lines += [f"**Blocked by:** {_safe_text(run.blocked_by)}", ""]

    for result in run.results:
        heading = result.role.value.replace("_", " ").title()
        lines += [f"## {heading}", _safe_text(result.summary), ""]
        if result.unknowns:
            lines += ["**Unknowns**"]
            lines += [f"- {_safe_text(u)}" for u in result.unknowns]
            lines += [""]
        if result.artifacts:
            lines += ["**Artifacts**"]
            lines += [f"- `{_safe_text(str(k))}`" for k in sorted(result.artifacts)]
            lines += [""]
    return "\n".join(lines)
