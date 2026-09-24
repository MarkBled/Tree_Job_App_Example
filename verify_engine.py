#!/usr/bin/env python3
"""Primerja izhod pogona TREE (out/tree_outputs.tsv) s Python/Kleene evalvacijo (out/odlocitev.json).

TREE-vrednost vozlišča: D-test protislovje -> T; O-test protislovje -> F; sicer U.
Rezultat: out/preverjanje_tree.json (vsak dokaz z izvirnim izhodom pogona).
"""
import json, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent


def main():
    rows = {}
    for line in (BASE / "out" / "tree_outputs.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        p = line.split("\t") + [""] * 6
        rows[p[0]] = {"formula": p[1], "celotna": p[2] == "true", "status": p[3], "implikanti": p[4], "minimalne": p[5]}
    dec = json.loads((BASE / "out" / "odlocitev.json").read_text(encoding="utf-8"))
    ok, bad, n = 0, [], 0
    for mode, r in dec["po_nacinu"].items():
        for k, c in r["kandidati"].items():
            for pr in c["dokazi"]:
                key = f"{mode}|{k}|{pr['vozlisce']}"
                d, o = rows.get(key + "|D"), rows.get(key + "|O")
                n += 1
                if not d or not o or not d["celotna"] or not o["celotna"] or "PARSE_ERROR" in (d["status"], o["status"]):
                    bad.append({"kljuc": key, "napaka": "manjka ali napaka parsiranja"})
                    continue
                tv = "T" if d["status"] == "CONTRADICTION" else ("F" if o["status"] == "CONTRADICTION" else "U")
                pr["tree"] = {"vrednost": tv, "D": d, "O": o}
                if tv == pr["python"]:
                    ok += 1
                else:
                    bad.append({"kljuc": key, "tree": tv, "python": pr["python"]})
    dec["preverjanje_tree"] = {"dokazov": n, "ujemanje": ok, "neujemanja": bad,
                               "vhodov": len(rows)}
    (BASE / "out" / "odlocitev.json").write_text(json.dumps(dec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"TREE ↔ Python: {ok}/{n} ujemanj, {len(bad)} neujemanj ({len(rows)} vhodov)")
    if bad:
        print(bad[:5])
        sys.exit(1)


if __name__ == "__main__":
    main()
