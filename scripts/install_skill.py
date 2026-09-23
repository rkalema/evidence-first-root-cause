#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil
from pathlib import Path

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('destination',type=Path); p.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]); a=p.parse_args()
    if a.destination.exists(): raise SystemExit(f'destination already exists: {a.destination}')
    shutil.copytree(a.source,a.destination,ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache'))
    print(a.destination); return 0
if __name__=='__main__': raise SystemExit(main())
