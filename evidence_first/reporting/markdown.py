from __future__ import annotations
from evidence_first.runtime.engine import InvestigationRun

def render_investigation_report(run:InvestigationRun)->str:
    lines=['# Evidence-First Investigation Report','',f'**Question:** {run.question}',f'**Stage:** {run.stage.value}','']
    if run.blocked_by: lines += [f'**Blocked by:** {run.blocked_by}','']
    for result in run.results:
        lines += [f'## {result.role.value.replace("_"," ").title()}',result.summary,'']
        if result.unknowns: lines += ['**Unknowns**']+[f'- {u}' for u in result.unknowns]+['']
        if result.artifacts: lines += ['**Artifacts**']+[f'- {k}' for k in sorted(result.artifacts)]+['']
    return '\n'.join(lines)
