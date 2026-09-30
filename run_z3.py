#!/usr/bin/env python3
"""Cevovod z jedrom Z3: python3 run_z3.py  (zahteva: pip install z3-solver)

candidates → facts → decide (TREE/Kleene, za primerjavo) → verify_engine (obstoječi izhod TREE)
→ z3_core → report_z3  ⇒  out/report_z3.html, out/zapis_z3.json, out/z3/*.smt2
"""
import subprocess, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
for s in ("candidates.py", "facts.py", "decide.py", "verify_engine.py", "z3_core.py", "report_z3.py"):
    print(f"> {s}")
    subprocess.run([sys.executable, "-B", str(BASE / s)], check=True)
