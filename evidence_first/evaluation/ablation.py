from __future__ import annotations

def ablation_plan()->tuple[dict[str,object],...]:
    return (
        {"name":"full_system","disabled":[]},
        {"name":"no_signal_validation","disabled":["signal_validator"]},
        {"name":"no_contradiction","disabled":["contradiction_investigator"]},
        {"name":"no_confound_review","disabled":["confound_reviewer"]},
        {"name":"no_critic","disabled":["critic"]},
        {"name":"skill_only","disabled":["runtime","tools","memory","domain_packs"]},
    )
