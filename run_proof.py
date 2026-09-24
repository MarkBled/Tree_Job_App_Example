#!/usr/bin/env python3
"""Celoten dokazni cevovod za prijave.

  python3 run_proof.py [--tree POT_DO_MAPE_Tree]

1 candidates.py  2 facts.py  3 decide.py
4 TREE: če sta na voljo javac (JDK 15+) in izvorna koda Tree, prevede HarnessProof v začasno mapo in ga zažene;
  sicer uporabi obstoječi out/tree_outputs.tsv (verify_engine.py zazna neskladje)
5 verify_engine.py  6 report.py
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
py = lambda s, *a: subprocess.run([sys.executable, str(BASE / s), *a], check=True)

tree_dir = Path(sys.argv[sys.argv.index("--tree") + 1]) if "--tree" in sys.argv else BASE.parent / "Tree"
for s in ("candidates.py", "facts.py", "decide.py"):
    print(f"> {s}"); py(s)

if shutil.which("javac") and (tree_dir / "propMinimization").exists():
    print("> TREE (izvirni pogon)")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        shutil.copytree(tree_dir, src)
        shutil.copy(BASE / "verify" / "HarnessProof.java", src / "propMinimization")
        cls = Path(tmp) / "cls"
        files = [str(p) for d in ("common", "propositional", "propMinimization") for p in (src / d).glob("*.java")]
        subprocess.run(["javac", "-nowarn", "-encoding", "UTF-8", "-d", str(cls), *files], check=True)
        subprocess.run(["java", "-Djava.awt.headless=true", "-cp", str(cls), "propMinimization.HarnessProof",
                        str(BASE / "out" / "tree_inputs.tsv"), str(BASE / "out" / "tree_outputs.tsv")], check=True)
else:
    print("> TREE: javac (JDK 15+) ali mapa Tree ni na voljo – uporabljam obstoječi out/tree_outputs.tsv")

for s in ("verify_engine.py", "report.py"):
    print(f"> {s}"); py(s)
