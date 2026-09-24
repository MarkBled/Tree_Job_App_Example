#!/usr/bin/env python3
"""Celoten cevovod: python3 run_all.py [pot/do/oglasa.pdf|.txt]"""
import subprocess, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
src = sys.argv[1:] or [str(BASE / "data" / "JobReqId26984690.pdf")]
for step in (["segment.py", *src], ["classify.py"], ["build_tree.py"], ["export_tree.py"]):
    print(f"> {step[0]}")
    subprocess.run([sys.executable, str(BASE / step[0]), *step[1:]], check=True)
