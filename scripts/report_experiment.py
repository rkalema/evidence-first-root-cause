#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv
from pathlib import Path
from evidence_first.evaluation.record import ExperimentLedger

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('ledger',type=Path); p.add_argument('--csv',dest='csv_path',type=Path); a=p.parse_args()
    rows=ExperimentLedger(a.ledger).read()
    by={}
    for r in rows: by.setdefault(r.condition,[]).append(r)
    print('# Experiment Summary')
    for condition,items in sorted(by.items()):
        mean=sum(x.score for x in items)/len(items) if items else 0
        rate=sum(x.passed for x in items)/len(items) if items else 0
        print(f'{condition}: n={len(items)}, mean_score={mean:.2f}, pass_rate={rate:.1%}')
    if a.csv_path:
        a.csv_path.parent.mkdir(parents=True,exist_ok=True)
        with a.csv_path.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].__dict__) if rows else ['case_id'])
            w.writeheader(); [w.writerow(r.__dict__) for r in rows]
    return 0
if __name__=='__main__': raise SystemExit(main())
